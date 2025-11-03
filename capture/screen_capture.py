import tkinter as tk
from PIL import ImageGrab, Image, ImageStat, ImageTk, ImageChops
import threading
import time
from typing import Callable, Tuple, List, Optional
from dataclasses import dataclass


def clamp(value: int, min_value: int, max_value: int) -> int:
	"""Clamp integer 'value' into the inclusive range [min_value, max_value]."""
	return max(min_value, min(value, max_value))


class DifferenceHash:
	"""Simple difference-hash (dHash) for change detection on small regions.

	- compute: builds a perceptual hash by comparing adjacent pixels in grayscale.
	- hamming_distance: counts differing bits between two hashes.
	"""

	@staticmethod
	def compute(image: Image.Image, hash_size: int = 8) -> int:
		"""Return integer dHash of an image. Smaller hash_size -> faster, less precise."""
		gray = image.convert('L').resize((hash_size + 1, hash_size), Image.BILINEAR)
		pixels = list(gray.getdata())
		rows = [pixels[i * (hash_size + 1):(i + 1) * (hash_size + 1)] for i in range(hash_size)]
		bits = 0
		bit_index = 0
		for row in rows:
			for x in range(hash_size):
				bits <<= 1
				bits |= 1 if row[x] > row[x + 1] else 0
				bit_index += 1
		return bits

	@staticmethod
	def hamming_distance(h1: int, h2: int) -> int:
		"""Return the number of differing bits between two integer hashes."""
		return (h1 ^ h2).bit_count()


class BlockComparator:
	"""Block-based brightness comparison for larger regions."""

	def __init__(self, grid_rows: int = 16, grid_cols: int = 16, change_threshold: float = 0.08, block_delta: float = 12.0):
		"""Initialize comparator.

		- grid_rows/grid_cols: grid resolution to summarize brightness per block.
		- change_threshold: minimal fraction of blocks that must change to flag change.
		- block_delta: minimal mean brightness delta per block to count as changed.
		"""
		self.grid_rows = grid_rows
		self.grid_cols = grid_cols
		self.change_threshold = change_threshold  # fraction of blocks that must change
		self.block_delta = block_delta  # minimum mean brightness difference per block
		self.prev_block_means: Optional[List[float]] = None

	def _compute_block_means(self, image: Image.Image) -> List[float]:
		"""Compute mean brightness for each block in a grid over the image."""
		w, h = image.size
		bw = max(1, w // self.grid_cols)
		bh = max(1, h // self.grid_rows)
		means: List[float] = []
		gray = image.convert('L')
		for gy in range(self.grid_rows):
			for gx in range(self.grid_cols):
				x1 = gx * bw
				y1 = gy * bh
				x2 = w if gx == self.grid_cols - 1 else (gx + 1) * bw
				y2 = h if gy == self.grid_rows - 1 else (gy + 1) * bh
				crop = gray.crop((x1, y1, x2, y2))
				means.append(float(ImageStat.Stat(crop).mean[0]))
		return means

	def is_changed(self, image: Image.Image) -> bool:
		"""Return True if enough blocks change compared to previous frame; update state."""
		current = self._compute_block_means(image)
		if self.prev_block_means is None:
			self.prev_block_means = current
			return True
		changed_blocks = 0
		total_blocks = len(current)
		for i in range(total_blocks):
			if abs(current[i] - self.prev_block_means[i]) >= self.block_delta:
				changed_blocks += 1
		fraction_changed = changed_blocks / max(1, total_blocks)
		self.prev_block_means = current
		return fraction_changed >= self.change_threshold


@dataclass
class Region:
	index: int
	coords: Tuple[int, int, int, int]  # (x1, y1, x2, y2)


class RegionWatcher:
	"""Watches a region using appropriate comparator based on size."""

	def __init__(self, region: Region, sensitivity: float = 0.7):
		"""Create watcher for a region.

		- sensitivity in [0,1]: higher -> more sensitive to small changes.
		"""
		self.region = region
		x1, y1, x2, y2 = region.coords
		self.width = max(0, x2 - x1)
		self.height = max(0, y2 - y1)
		self.small_threshold_px = 200
		self.prev_hash: Optional[int] = None
		# Sensitivity in [0,1]; higher means more sensitive to small changes
		self.sensitivity = max(0.0, min(1.0, sensitivity))
		# Tune block comparator thresholds by sensitivity
		block_delta = 12.0 * (1.0 - 0.6 * self.sensitivity)  # 12 -> ~4.8
		change_fraction = 0.08 * (1.0 - 0.5 * self.sensitivity)  # 0.08 -> ~0.04
		self.block_comparator = BlockComparator(change_threshold=change_fraction, block_delta=block_delta)
		# Low-res quick check cache
		self._prev_lowres: Optional[Image.Image] = None

	def has_changed(self, cropped: Image.Image) -> bool:
		"""Check whether the region image changed since previous frame.

		Pipeline:
		1) Quick low-res grayscale diff to early-exit when nearly identical.
		2) If small region: perceptual hash (dHash) with Hamming threshold.
		3) Else: block-based brightness comparator with tuned thresholds.
		"""
		# Quick low-res difference check to catch subtle changes cheaply
		try:
			gray = cropped.convert('L')
			lowres = gray.resize((32, 32), Image.BILINEAR)
			if self._prev_lowres is not None:
				diff = ImageChops.difference(lowres, self._prev_lowres)
				mean_diff = float(ImageStat.Stat(diff).mean[0])
				# Lower epsilon at higher sensitivity (more sensitive)
				epsilon = 2.5 * (1.0 - self.sensitivity) + 0.6
				if mean_diff < epsilon:
					return False
			self._prev_lowres = lowres
		except Exception:
			self._prev_lowres = None

		if self.width < self.small_threshold_px and self.height < self.small_threshold_px:
			cur_hash = DifferenceHash.compute(cropped)
			if self.prev_hash is None:
				self.prev_hash = cur_hash
				return True
			dist = DifferenceHash.hamming_distance(self.prev_hash, cur_hash)
			self.prev_hash = cur_hash
			# dHash threshold: 1 at high sensitivity, 2 at low
			return dist >= (1 if self.sensitivity >= 0.5 else 2)
		return self.block_comparator.is_changed(cropped)



class MultiRegionMonitor:
	def __init__(self, regions: List[Tuple[int, int, int, int]], fps: int = 8, on_region_change: Optional[Callable[[int, Image.Image, int], None]] = None, on_scan: Optional[Callable[[int], None]] = None, logical_screen_size: Optional[Tuple[int, int]] = None, sensitivity: float = 0.7):
		"""Monitor multiple regions by grabbing full screen and cropping per frame.

		- on_region_change: callback(idx, cropped_image, scan_counter) when changed.
		- on_scan: callback(scan_counter) after each frame.
		- logical_screen_size: Tk logical size to compensate DPI scaling.
		- sensitivity: forwarded to RegionWatcher.
		"""
		self.regions = [Region(index=i, coords=r) for i, r in enumerate(regions)]
		self.watchers = [RegionWatcher(region=r, sensitivity=sensitivity) for r in self.regions]
		self.fps = clamp(fps, 1, 30)
		self.frame_interval = 1.0 / self.fps
		self._stop_event = threading.Event()
		self.scan_counter = 0
		self.on_region_change = on_region_change
		self.on_scan = on_scan
		self.logical_screen_size = logical_screen_size
		self._scale_x = 1.0
		self._scale_y = 1.0
		self._thread: Optional[threading.Thread] = None

	def start(self):
		"""Start the monitoring loop on a background daemon thread."""
		if self._thread and self._thread.is_alive():
			return
		self._stop_event.clear()
		self._thread = threading.Thread(target=self._run_loop, daemon=True)
		self._thread.start()

	def stop(self, join: bool = True):
		"""Signal the loop to stop; optionally wait briefly for thread to exit."""
		self._stop_event.set()
		# Nudge any sleep to wake quickly
		try:
			# Small wait to let loop break promptly
			time.sleep(0.01)
		except Exception:
			pass
		if join and self._thread and self._thread.is_alive():
			try:
				self._thread.join(timeout=2.5)
			except Exception:
				pass

	def _run_loop(self):
		"""Background loop: grab full screen, crop regions, detect changes, callback."""
		print(f"[Monitor] Starting with {len(self.regions)} regions at {self.fps} fps")
		while not self._stop_event.is_set():
			start_time = time.time()
			try:
				full = ImageGrab.grab()
			except Exception:
				# If grabbing fails (window switching), small sleep and continue
				time.sleep(0.01)
				continue
			fw, fh = full.size
			if self.logical_screen_size:
				lw, lh = self.logical_screen_size
				if lw > 0 and lh > 0:
					self._scale_x = fw / lw
					self._scale_y = fh / lh
			for watcher in self.watchers:
				x1, y1, x2, y2 = watcher.region.coords
				sx1 = int(round(x1 * self._scale_x))
				sy1 = int(round(y1 * self._scale_y))
				sx2 = int(round(x2 * self._scale_x))
				sy2 = int(round(y2 * self._scale_y))
				# clamp within full image bounds
				sx1 = clamp(sx1, 0, fw)
				sy1 = clamp(sy1, 0, fh)
				sx2 = clamp(sx2, 0, fw)
				sy2 = clamp(sy2, 0, fh)
				if sx2 <= sx1 or sy2 <= sy1:
					continue
				crop = full.crop((sx1, sy1, sx2, sy2))
				if watcher.has_changed(crop):
					if self.on_region_change is not None:
						try:
							self.on_region_change(watcher.region.index, crop, self.scan_counter)
						except Exception:
							pass
			self.scan_counter += 1
			if self.on_scan is not None:
				try:
					self.on_scan(self.scan_counter)
				except Exception:
					pass
			elapsed = time.time() - start_time
			to_sleep = self.frame_interval - elapsed
			if to_sleep > 0:
				# Wait that can be interrupted by stop to avoid UI hang on stop
				if self._stop_event.wait(to_sleep):
					break
		# loop exits when stop_event is set


class ScreenCapture:
	def __init__(self, on_capture: Callable[[Tuple[int, int, int, int]], None] = None, on_region_change: Optional[Callable[[int, Image.Image, int], None]] = None):
		"""UI flow to select multiple regions, then start real-time region monitoring.

		- on_capture: callback mỗi lần người dùng chọn xong một vùng.
		- on_region_change: callback khi vùng thay đổi (idx, PIL.Image, scan_counter).
		"""
		self.on_capture = on_capture
		self.on_region_change = on_region_change
		self.start_x = self.start_y = 0
		self.canvas = None
		self.rect_id = None
		self.capture_window = None
		self.captured_coords: List[Tuple[int, int, int, int]] = []

	def start_capture(self):
		"""Start region selection flow (can repeat to select multiple regions)."""
		self._capture_loop()
		self.root.mainloop()

	def _capture_loop(self):
		"""Open a translucent fullscreen overlay to draw a selection rectangle."""
		# Nếu root đã tồn tại -> tạo cửa sổ mới bằng Toplevel
		if hasattr(self, "root") and self.root:
			self.capture_window = tk.Toplevel(self.root)
		else:
			self.root = tk.Tk()
			self.root.withdraw()  # ẩn cửa sổ gốc
			self.capture_window = tk.Toplevel(self.root)

		self.capture_window.attributes('-fullscreen', True)
		self.capture_window.attributes('-alpha', 0.3)
		self.capture_window.configure(background='black')

		# canvas để vẽ vùng chọn
		self.canvas = tk.Canvas(self.capture_window, cursor="cross", bg="black")
		self.canvas.pack(fill="both", expand=True)

		self.canvas.bind('<ButtonPress-1>', self.on_button_press)
		self.canvas.bind('<B1-Motion>', self.on_move_press)
		self.canvas.bind('<ButtonRelease-1>', self.on_button_release)

	def on_button_press(self, event):
		"""Begin drawing selection rectangle at mouse-down position."""
		self.start_x = event.x
		self.start_y = event.y
		# reset rectangle mới
		if self.rect_id:
			self.canvas.delete(self.rect_id)
		self.rect_id = self.canvas.create_rectangle(
			self.start_x, self.start_y, self.start_x, self.start_y,
			outline="red", width=2
		)

	def on_move_press(self, event):
		"""Update selection rectangle while dragging."""
		curX, curY = (event.x, event.y)
		# chỉ update toạ độ thay vì delete all
		if self.rect_id:
			self.canvas.coords(self.rect_id, self.start_x, self.start_y, curX, curY)

	def on_button_release(self, event):
		"""Finalize rectangle on mouse-up and proceed with selection flow."""
		end_x, end_y = (event.x, event.y)
		x1 = min(self.start_x, end_x)
		y1 = min(self.start_y, end_y)
		x2 = max(self.start_x, end_x)
		y2 = max(self.start_y, end_y)

		# đóng cửa sổ chọn
		self.capture_window.destroy()

		threading.Thread(target=self._capture_and_callback, args=(x1, y1, x2, y2), daemon=True).start()

	def _capture_and_callback(self, x1: int, y1: int, x2: int, y2: int):
		"""Store selected coords; ask user to continue or proceed to monitoring."""
		# Lưu toạ độ, không cần chụp từng vùng ngay tại đây để tiết kiệm hiệu năng
		self.captured_coords.append((x1, y1, x2, y2))
		if self.on_capture:
			self.on_capture((x1, y1, x2, y2))
		# Hỏi tiếp tục hay không
		if self._ask_continue():
			self._capture_loop()
		else:
			# Chạy phần mở viewer/monitor trên main thread (Tk) để tránh lỗi apartment
			try:
				self.root.after(0, self._process_captures)
			except Exception:
				# Fallback nếu root chưa sẵn sàng
				self._process_captures()

	def _ask_continue(self) -> bool:
		"""Ask whether to select another region (Yes) or start monitoring (No)."""
		import tkinter.messagebox as mb
		return mb.askyesno("Tiếp tục?", "Bạn có muốn chọn vùng tiếp theo không?")

	def _process_captures(self):
		"""After selection finishes, open viewer and start the monitor."""
		print("Các vùng đã chọn:", self.captured_coords)
		if not self.captured_coords:
			print("[Monitor] Không có vùng nào để theo dõi.")
			return
		# Tạo UI hiển thị vùng và nút dừng
		self._open_viewer(self.captured_coords)

	def _open_viewer(self, regions: List[Tuple[int, int, int, int]]):
		"""Create the viewer window and wire callbacks to the monitor."""
		self._viewer = RegionViewer(self.root, regions)
		self._monitor = MultiRegionMonitor(
			regions,
			fps=15,
			on_region_change=lambda idx, img, scan: self._handle_region_change(idx, img, scan),
			on_scan=lambda scan: self._viewer.update_scan_counter(scan),
			logical_screen_size=self._get_logical_screen_size(),
			sensitivity=0.6,
		)
		# Ensure the monitor thread is stopped when viewer stops
		self._viewer.set_stop_callback(lambda: self._monitor.stop(join=True))
		self._monitor.start()
		self._viewer.show()

	def _handle_region_change(self, idx: int, img: Image.Image, scan: int):
		"""Forward region image to viewer and external callback (if any)."""
		try:
			self._viewer.enqueue_update(idx, img)
		except Exception:
			pass
		if self.on_region_change is not None:
			try:
				self.on_region_change(idx, img, scan)
			except Exception:
				pass

	def _get_logical_screen_size(self) -> Tuple[int, int]:
		"""Return Tk logical screen size used for DPI scaling compensation."""
		# Use the fullscreen selection window size as logical size reference
		try:
			# If capture_window is alive use its size, else fall back to root.winfo_screenwidth/height
			if self.capture_window and str(self.capture_window) != ".!toplevel" and self.capture_window.winfo_exists():
				return (self.capture_window.winfo_screenwidth(), self.capture_window.winfo_screenheight())
		except Exception:
			pass
		try:
			return (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
		except Exception:
			return (0, 0)


class RegionViewer:
	"""Tk viewer window that shows live thumbnails per region and a Stop button."""

	def __init__(self, root: tk.Misc, regions: List[Tuple[int, int, int, int]]):
		"""Build the viewer UI with a grid of thumbnails and a stop button."""
		self.root = root
		self.regions = regions
		self.win = tk.Toplevel(self.root)
		self.win.title("Region Monitor")
		self.win.protocol("WM_DELETE_WINDOW", self._on_close)
		self.frames: List[tk.Frame] = []
		self.labels: List[tk.Label] = []
		self.photo_images: List[Optional[ImageTk.PhotoImage]] = [None] * len(regions)
		self.stop_callback: Optional[Callable[[], None]] = None
		self._stopped = False
		self.scan_var = tk.StringVar(value="Scans: 0")

		# Layout
		info_bar = tk.Frame(self.win)
		info_bar.pack(fill="x")
		self.scan_label = tk.Label(info_bar, textvariable=self.scan_var)
		self.scan_label.pack(side="left", padx=6, pady=4)
		self.stop_btn = tk.Button(info_bar, text="Dừng theo dõi", command=self._on_stop)
		self.stop_btn.pack(side="right", padx=6, pady=4)

		grid = tk.Frame(self.win)
		grid.pack(fill="both", expand=True)

		cols = max(1, int(len(regions) ** 0.5))
		for i in range(len(regions)):
			frame = tk.Frame(grid, bd=1, relief="sunken")
			row = i // cols
			col = i % cols
			frame.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
			for c in range(cols):
				grid.grid_columnconfigure(c, weight=1)
			grid.grid_rowconfigure(row, weight=1)
			label = tk.Label(frame, text=f"Region {i}")
			label.pack()
			img_label = tk.Label(frame)
			img_label.pack()
			self.frames.append(frame)
			self.labels.append(img_label)

		self._queue: List[Tuple[int, Image.Image]] = []
		self._queue_lock = threading.Lock()
		# Store after id to allow canceling on stop/close
		self._after_id: Optional[str] = None
		self._update_ui_loop()

	def set_stop_callback(self, cb: Callable[[], None]):
		"""Set the callback invoked when user clicks Stop or closes the window."""
		self.stop_callback = cb

	def enqueue_update(self, idx: int, image: Image.Image):
		"""Queue an updated image for region 'idx' to be shown on the UI thread."""
		if self._stopped:
			return
		thumb = self._make_thumbnail(image)
		with self._queue_lock:
			self._queue.append((idx, thumb))

	def update_scan_counter(self, scans: int):
		"""Update the visible scan counter label."""
		self.scan_var.set(f"Scans: {scans}")

	def show(self):
		"""Show the viewer window (mainloop already runs in the app)."""
		self.win.deiconify()
		self.win.lift()
		self.win.focus_force()
		# Không gọi mainloop ở đây; mainloop đã chạy từ ScreenCapture.start_capture

	def _make_thumbnail(self, image: Image.Image) -> Image.Image:
		"""Create a small thumbnail to display for the region image."""
		max_w, max_h = 240, 240
		img = image.copy()
		img.thumbnail((max_w, max_h), Image.BILINEAR)
		return img

	def _update_ui_loop(self):
		"""Periodic UI task that flushes the image queue to the labels."""
		# Process queued updates on main thread
		with self._queue_lock:
			items = list(self._queue)
			self._queue.clear()
		for idx, img in items:
			if 0 <= idx < len(self.labels):
				photo = ImageTk.PhotoImage(img)
				self.photo_images[idx] = photo  # keep reference to avoid GC
				self.labels[idx].configure(image=photo)
		# Only reschedule if not stopped and window still exists
		if not self._stopped and self.win.winfo_exists():
			self._after_id = self.win.after(50, self._update_ui_loop)

	def _on_stop(self):
		"""Handle Stop click: stop monitor and close the window."""
		self._stopped = True
		if self.stop_callback:
			try:
				self.stop_callback()
			except Exception:
				pass
		self._on_close()

	def _on_close(self):
		"""Destroy the viewer and cancel any scheduled callbacks."""
		self._stopped = True
		# Cancel any scheduled callbacks to avoid lingering after loops
		try:
			if getattr(self, "_after_id", None) is not None and self.win.winfo_exists():
				self.win.after_cancel(self._after_id)
		except Exception:
			pass
		try:
			self.win.destroy()
		except Exception:
			pass
		# Attempt to quit the Tk mainloop if root is present
		try:
			self.root.quit()
		except Exception:
			pass
		# Ensure the root is destroyed to fully exit the UI loop
		try:
			self.root.destroy()
		except Exception:
			pass


def my_callback(coords):
    print("Vùng đã chọn:", coords)


if __name__ == "__main__":
    sc = ScreenCapture(on_capture=my_callback)
    sc.start_capture()