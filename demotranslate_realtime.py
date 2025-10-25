"""
Demo Realtime Translation System
Test the optimized realtime translation manager
"""

import os
import time
import asyncio
from typing import Dict, List, Optional
from translation.translation_manager_realtime import RealtimeTranslationManager
from translation.config import TranslationConfig


class DemoRealtimeTranslation:
    """Demo class để test realtime translation manager"""

    def __init__(self):
        print("=== Demo Realtime Translation System ===")

        # Khởi tạo realtime translation system
        self.config = TranslationConfig('config.env')
        self.manager = RealtimeTranslationManager({
            'gemini_api_key': self.config.get_api_key('gemini')
        }, realtime_mode=True)

        # Preload common models for instant translation
        self.manager.preload_common_models()

        # Test data
        self.test_texts = {
            'en': [
                "Hello world",
                "This is a test message",
                "How are you today?",
                "The weather is nice today",
                "I love programming"
            ],
            'fr': [
                "Bonjour le monde",
                "Ceci est un message de test",
                "Comment allez-vous aujourd'hui?",
                "Le temps est beau aujourd'hui",
                "J'aime la programmation"
            ],
            'ja': [
                "Konnichiwa sekai",
                "Kore wa test message desu",
                "Kyou wa dou desu ka?",
                "Kyou wa tenki ga ii desu",
                "Programming ga suki desu"
            ],
            'zh': [
                "Ni hao shi jie",
                "Zhe shi yi ge ce shi xiao xi",
                "Ni jin tian zen me yang?",
                "Jin tian tian qi hen hao",
                "Wo xi huan bian cheng"
            ],
            'vi': [
                "Xin chao the gioi",
                "Day la tin nhan thu nghiem",
                "Hom nay ban the nao?",
                "Hom nay thoi tiet dep",
                "Toi thich lap trinh"
            ]
        }

        self.target_languages = ['en', 'fr', 'ja', 'zh', 'vi']

        print(f"Available models: {self.manager.get_available_models()}")
        print(f"Supported languages: {self.manager.get_supported_languages()}")
        print(f"Supported pairs: {len(self.manager.get_supported_pairs())}")
        print(f"Realtime mode: {self.manager.realtime_mode}")
        print(f"Confidence threshold: {self.manager.confidence_threshold}")

    def test_single_translation(self, text: str, source_lang: str, target_lang: str):
        """Test dịch một text cụ thể"""
        print(f"\n--- Testing Single Translation ---")
        print(f"Text: '{text}'")
        print(f"Source: {source_lang} -> Target: {target_lang}")

        start_time = time.time()
        result = self.manager.translate(text, source_lang, target_lang)
        end_time = time.time()

        if result:
            try:
                print(f"[OK] Translated: '{result['text']}'")
            except UnicodeEncodeError:
                print(f"[OK] Translated: {result['text'].encode('ascii', 'replace').decode('ascii')}")
            print(f"[OK] Model: {result.get('model_used', 'unknown')}")
            print(f"[OK] Confidence: {result.get('confidence', 0):.2f}")
            print(f"[OK] Time: {end_time - start_time:.2f}s")
        else:
            print("[ERROR] Translation failed")

        return result

    def test_parallel_performance(self):
        """Test hiệu suất parallel translation"""
        print(f"\n--- Testing Parallel Translation Performance ---")

        test_text = "Hello world, this is a test message for performance comparison."
        source_lang = 'en'
        target_lang = 'vi'

        print(f"Test text: '{test_text}'")
        print(f"Translation: {source_lang} -> {target_lang}")

        # Test multiple times to see parallel benefits
        times = []
        for i in range(5):
            start_time = time.time()
            result = self.manager.translate(test_text, source_lang, target_lang)
            end_time = time.time()
            times.append(end_time - start_time)
            print(f"Run {i+1}: {end_time - start_time:.3f}s")

        avg_time = sum(times) / len(times)
        print(f"Average time: {avg_time:.3f}s")
        print(f"Min time: {min(times):.3f}s")
        print(f"Max time: {max(times):.3f}s")

    def test_pivot_translation(self):
        """Test pivot translation for unsupported pairs"""
        print(f"\n--- Testing Pivot Translation ---")

        pivot_tests = [
            ("Xin chao", 'vi', 'ja'),  # Vietnamese to Japanese via English
            ("Bonjour", 'fr', 'zh'),   # French to Chinese via English
            ("Hello", 'en', 'vi'),     # English to Vietnamese (direct)
        ]

        for text, src, tgt in pivot_tests:
            print(f"\nPivot test: '{text}' ({src} -> {tgt})")
            start_time = time.time()
            result = self.manager.translate(text, src, tgt)
            end_time = time.time()

            if result:
                print(f"[OK] Result: '{result['text']}' (Model: {result.get('model_used', 'unknown')})")
                print(f"[OK] Time: {end_time - start_time:.2f}s")
            else:
                print("[ERROR] Pivot translation failed")

    async def test_async_translation(self):
        """Test async translation capabilities"""
        print(f"\n--- Testing Async Translation ---")

        texts = [
            "Hello world",
            "Bonjour le monde",
            "Xin chao the gioi",
            "Ni hao shi jie",
            "Konnichiwa sekai"
        ]

        print("Testing async batch translation...")
        start_time = time.time()
        results = await self.manager.translate_batch_async(texts, 'auto', 'en')
        end_time = time.time()

        print(f"Batch translation completed in {end_time - start_time:.3f}s")
        for i, result in enumerate(results):
            if result:
                print(f"  {i+1}. '{texts[i]}' -> '{result['text']}'")
            else:
                print(f"  {i+1}. '{texts[i]}' -> [FAILED]")

    def test_cache_performance(self):
        """Test caching performance"""
        print(f"\n--- Testing Cache Performance ---")

        test_text = "This is a cached test message"
        source_lang = 'en'
        target_lang = 'vi'

        # First translation (cache miss)
        print("First translation (cache miss):")
        start_time = time.time()
        result1 = self.manager.translate(test_text, source_lang, target_lang)
        time1 = time.time() - start_time

        # Second translation (cache hit)
        print("Second translation (cache hit):")
        start_time = time.time()
        result2 = self.manager.translate(test_text, source_lang, target_lang)
        time2 = time.time() - start_time

        print(f"Cache miss time: {time1:.3f}s")
        print(f"Cache hit time: {time2:.3f}s")
        if time2 > 0:
            print(f"Speedup: {time1/time2:.1f}x faster")
        else:
            print("Speedup: Instant (cache hit)")

        # Check cache stats
        stats = self.manager.get_stats()
        print(f"Cache size: {stats['cache_size']}")
        print(f"Detection cache size: {stats['detection_cache_size']}")

    def test_realtime_optimization(self):
        """Test realtime-specific optimizations"""
        print(f"\n--- Testing Realtime Optimizations ---")

        # Test with different confidence thresholds
        test_text = "Hello world"
        source_lang = 'en'
        target_lang = 'vi'

        print(f"Testing with confidence threshold: {self.manager.confidence_threshold}")

        start_time = time.time()
        result = self.manager.translate(test_text, source_lang, target_lang)
        end_time = time.time()

        if result:
            print(f"[OK] Result: '{result['text']}' (confidence: {result.get('confidence', 0):.2f})")
            print(f"[OK] Time: {end_time - start_time:.3f}s")
            print(f"[OK] Model used: {result.get('model_used', 'unknown')}")
        else:
            print("[ERROR] Translation failed")

    def run_full_demo(self):
        """Chạy demo đầy đủ"""
        print("Starting realtime demo...")

        # 1. Test single translation
        self.test_single_translation("Hello world", 'en', 'vi')

        # 2. Test parallel performance
        self.test_parallel_performance()

        # 3. Test pivot translation
        self.test_pivot_translation()

        # 4. Test cache performance
        self.test_cache_performance()

        # 5. Test realtime optimizations
        self.test_realtime_optimization()

        # 6. Skip async test (timeout issues)
        print("\n--- Skipping Async Translation Test (timeout issues) ---")

        # 7. Summary
        self.print_summary()

    def run_quick_demo(self):
        """Chạy demo dịch nhanh với 5 cặp ngôn ngữ"""
        print("\n--- Quick Realtime Translation Demo ---")

        test_text = "Hello, how are you today?"
        language_pairs = [
            ('en', 'vi'), ('vi', 'en'),
            ('zh', 'en'), ('ja', 'en'), ('fr', 'en')
        ]

        print(f"Translating '{test_text}' across multiple pairs:")

        for source_lang, target_lang in language_pairs:
            start_time = time.time()
            result = self.manager.translate(test_text, source_lang, target_lang)
            end_time = time.time()

            if result:
                print(f"  {source_lang}->{target_lang}: '{result['text']}' ({end_time - start_time:.2f}s)")
            else:
                print(f"  {source_lang}->{target_lang}: [ERROR] Failed")

    def test_model_comparison(self):
        """Test và so sánh tất cả models cho cùng một cặp ngôn ngữ"""
        print(f"\n--- Testing Model Comparison ---")

        # Chọn cặp ngôn ngữ để test
        test_text = "Hello world, this is a comprehensive test message for comparing translation models."
        source_lang = 'en'
        target_lang = 'vi'

        print(f"Test text: '{test_text}'")
        print(f"Language pair: {source_lang} -> {target_lang}")
        print("\n" + "="*80)

        # Test từng model
        models_to_test = ['nllb', 'opus', 'gemini']
        results = {}

        for model_name in models_to_test:
            print(f"\n🔍 Testing {model_name.upper()} Model:")
            print("-" * 40)

            try:
                start_time = time.time()
                result = self.manager.translate_with_model(test_text, source_lang, target_lang, model_name)
                end_time = time.time()

                if result:
                    results[model_name] = {
                        'text': result['text'],
                        'time': end_time - start_time,
                        'confidence': result.get('confidence', 0),
                        'model': result.get('model_used', model_name)
                    }

                    print(f"✅ SUCCESS:")
                    print(f"   Translation: '{result['text']}'")
                    print(f"   Time: {end_time - start_time:.3f}s")
                    print(f"   Confidence: {result.get('confidence', 0):.2f}")
                    print(f"   Model: {result.get('model_used', model_name)}")
                else:
                    print(f"❌ FAILED: {model_name} returned None")
                    results[model_name] = None

            except Exception as e:
                print(f"❌ ERROR: {model_name} failed with: {e}")
                results[model_name] = None

        # So sánh kết quả
        print(f"\n" + "="*80)
        print("📊 MODEL COMPARISON RESULTS")
        print("="*80)

        successful_models = {k: v for k, v in results.items() if v is not None}

        if successful_models:
            # Sort by time
            sorted_by_time = sorted(successful_models.items(), key=lambda x: x[1]['time'])

            print("\n⏱️  BY SPEED (Fastest to Slowest):")
            for i, (model, data) in enumerate(sorted_by_time, 1):
                print(f"   {i}. {model.upper()}: {data['time']:.3f}s")

            # Sort by confidence
            sorted_by_confidence = sorted(successful_models.items(), key=lambda x: x[1]['confidence'], reverse=True)

            print("\n🎯 BY CONFIDENCE (Highest to Lowest):")
            for i, (model, data) in enumerate(sorted_by_confidence, 1):
                print(f"   {i}. {model.upper()}: {data['confidence']:.2f}")

            # Show all translations
            print("\n📝 ALL TRANSLATIONS:")
            for model, data in successful_models.items():
                print(f"\n   {model.upper()}:")
                print(f"   '{data['text']}'")
                print(f"   (Time: {data['time']:.3f}s, Confidence: {data['confidence']:.2f})")

            # Performance summary
            fastest = sorted_by_time[0]
            slowest = sorted_by_time[-1]
            speedup = slowest[1]['time'] / fastest[1]['time'] if fastest[1]['time'] > 0 else float('inf')

            print("\n🚀 PERFORMANCE SUMMARY:")
            print(f"   Fastest: {fastest[0].upper()} ({fastest[1]['time']:.3f}s)")
            print(f"   Slowest: {slowest[0].upper()} ({slowest[1]['time']:.3f}s)")
            if speedup != float('inf'):
                print(f"   Speed difference: {speedup:.1f}x")
            else:
                print("   Speed difference: Instant vs slow")

        else:
            print("❌ No models succeeded!")

        failed_models = [k for k, v in results.items() if v is None]
        if failed_models:
            print(f"\n❌ Failed models: {', '.join(failed_models).upper()}")

    def print_summary(self):
        """In tóm tắt kết quả"""
        print(f"\n=== REALTIME TRANSLATION SUMMARY ===")

        stats = self.manager.get_stats()
        print(f"\nSystem Stats:")
        print(f"  - Realtime mode: {stats['realtime_mode']}")
        print(f"  - Confidence threshold: {stats['confidence_threshold']}")
        print(f"  - Cache size: {stats['cache_size']}")
        print(f"  - Detection cache size: {stats['detection_cache_size']}")
        print(f"  - Available models: {stats['available_models']}")

        print(f"\nModel Status:")
        for model_name, model_info in stats['models'].items():
            status = "[OK]" if model_info['available'] else "[ERROR]"
            print(f"  - {model_name}: {status} ({model_info['type']})")

        print(f"\nOptimizations Applied:")
        print("  ✓ Parallel model execution")
        print("  ✓ Layered OPUS loading")
        print("  ✓ Thread-safe caching")
        print("  ✓ Async support")
        print("  ✓ Language detection caching")
        print("  ✓ Pivot translation fallback")

        print(f"\nRecommendations:")
        print("  - Use for realtime applications requiring fast translation")
        print("  - Preload common language pairs at startup")
        print("  - Monitor cache sizes for memory usage")
        print("  - Use async methods for non-blocking operations")


def main():
    """Main function"""
    print("Realtime Translation System Demo")
    print("=" * 50)

    # Load config và kiểm tra API key
    config = TranslationConfig('config.env')
    api_key = config.get_api_key('gemini')

    if api_key:
        print(f"[OK] Gemini API key found: {api_key[:10]}...")
    else:
        print("[WARNING] Gemini API key not found")
        print("Continuing with offline models only...")

    try:
        demo = DemoRealtimeTranslation()

        # Chọn loại test
        print("\nChoose test type:")
        print("1. Full realtime demo (all tests)")
        print("2. Single translation test")
        print("3. Parallel performance test")
        print("4. Pivot translation test")
        print("5. Cache performance test")
        print("6. Async translation test")
        print("7. Quick realtime demo")
        print("8. System stats")
        print("9. Model comparison test")

        choice = input("\nEnter choice (1-9): ").strip()

        if choice == '1':
            demo.run_full_demo()
        elif choice == '2':
            text = input("Enter text to translate: ").strip()
            source = input("Enter source language (en/fr/ja/zh/vi): ").strip()
            target = input("Enter target language (en/fr/ja/zh/vi): ").strip()
            demo.test_single_translation(text, source, target)
        elif choice == '3':
            demo.test_parallel_performance()
        elif choice == '4':
            demo.test_pivot_translation()
        elif choice == '5':
            demo.test_cache_performance()
        elif choice == '6':
            asyncio.run(demo.test_async_translation())
        elif choice == '7':
            demo.run_quick_demo()
        elif choice == '8':
            stats = demo.manager.get_stats()
            print("\nSystem Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        elif choice == '9':
            demo.test_model_comparison()
        else:
            print("Invalid choice. Running full demo...")
            demo.run_full_demo()

        print("\n=== Demo Completed ===")

    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
