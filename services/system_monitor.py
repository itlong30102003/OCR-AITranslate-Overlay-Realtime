"""System Monitor - Real-time system metrics monitoring"""

import psutil
import threading
import time
from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal


class SystemMetrics:
    """Data class for system metrics"""
    def __init__(self):
        self.cpu_percent: float = 0.0
        self.memory_percent: float = 0.0
        self.gpu_percent: float = 0.0
        self.translation_speed_ms: int = 0


class SystemMonitor(QObject):
    """Monitor system resources and emit updates"""
    
    # Signal emitted when metrics are updated
    metrics_updated = pyqtSignal(object)  # Emits SystemMetrics
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.metrics = SystemMetrics()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._update_interval = 2.0  # Update every 2 seconds
        
        # Translation timing
        self._last_translation_times = []  # List of recent translation times in ms
        
        # Check if GPU monitoring is available
        self._gpu_available = False
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                self._gpu_available = True
                print(f"[SystemMonitor] GPU detected: {gpus[0].name}")
        except ImportError:
            print("[SystemMonitor] GPUtil not installed, GPU monitoring disabled")
        except Exception as e:
            print(f"[SystemMonitor] GPU detection failed: {e}")
    
    def start(self):
        """Start monitoring in background thread"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("[SystemMonitor] Started monitoring")
    
    def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
        print("[SystemMonitor] Stopped monitoring")
    
    def record_translation_time(self, time_ms: int):
        """Record a translation time for averaging"""
        self._last_translation_times.append(time_ms)
        # Keep only last 10 translations
        if len(self._last_translation_times) > 10:
            self._last_translation_times.pop(0)
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self._running:
            try:
                # CPU usage (average over 0.5 second)
                self.metrics.cpu_percent = psutil.cpu_percent(interval=0.5)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.metrics.memory_percent = memory.percent
                
                # GPU usage (if available)
                if self._gpu_available:
                    try:
                        import GPUtil
                        gpus = GPUtil.getGPUs()
                        if gpus:
                            self.metrics.gpu_percent = gpus[0].load * 100
                    except:
                        pass
                
                # Average translation speed
                if self._last_translation_times:
                    self.metrics.translation_speed_ms = int(
                        sum(self._last_translation_times) / len(self._last_translation_times)
                    )
                
                # Emit signal for UI update
                self.metrics_updated.emit(self.metrics)
                
                # Wait for next update
                time.sleep(self._update_interval)
                
            except Exception as e:
                print(f"[SystemMonitor] Error in monitor loop: {e}")
                time.sleep(1.0)
    
    def get_current_metrics(self) -> SystemMetrics:
        """Get current metrics snapshot"""
        return self.metrics


# Global instance - will be initialized when first imported in Qt context
system_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """Get or create the system monitor singleton"""
    global system_monitor
    if system_monitor is None:
        system_monitor = SystemMonitor()
    return system_monitor
