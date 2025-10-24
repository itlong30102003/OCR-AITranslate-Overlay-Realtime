"""
Demo Translation System
Test các mô hình dịch thuật trước khi tích hợp vào main
"""

import os
import time
from typing import Dict, List, Optional
from translation import TranslationManager
from translation.config import TranslationConfig


class DemoTranslation:
    """Demo class để test các mô hình translation"""
    
    def __init__(self):
        print("=== Demo Translation System ===")
        
        # Khởi tạo translation system
        self.config = TranslationConfig('config.env')
        self.manager = TranslationManager({
            'gemini_api_key': self.config.get_api_key('gemini')
        })
        
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
        print(f"Supported pairs: {len(self.manager.get_supported_pairs())} pairs")
    
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
    
    def test_auto_detection(self):
        """Test phát hiện ngôn ngữ tự động"""
        print(f"\n--- Testing Auto Language Detection ---")
        
        for lang, texts in self.test_texts.items():
            for text in texts[:2]:  # Test 2 text mỗi ngôn ngữ
                print(f"\nText: '{text}'")
                result = self.manager.translate(text, 'auto', 'vi')
                if result:
                    try:
                        print(f"[OK] Detected -> Translated: '{result['text']}'")
                    except UnicodeEncodeError:
                        print(f"[OK] Detected -> Translated: {result['text'].encode('ascii', 'replace').decode('ascii')}")
                    print(f"[OK] Model: {result.get('model_used', 'unknown')}")
                else:
                    print("[ERROR] Auto detection failed")
    
    def test_all_models(self, text: str, source_lang: str, target_lang: str):
        """Test tất cả các mô hình có sẵn"""
        print(f"\n--- Testing All Available Models ---")
        print(f"Text: '{text}' ({source_lang} -> {target_lang})")
        
        available_models = self.manager.get_available_models()
        results = {}
        
        for model in available_models:
            print(f"\nTesting {model}:")
            start_time = time.time()
            
            try:
                result = self.manager.translate_with_model(text, source_lang, target_lang, model)
                end_time = time.time()
                
                if result:
                    try:
                        print(f"[OK] Result: '{result['text']}'")
                    except UnicodeEncodeError:
                        print(f"[OK] Result: {result['text'].encode('ascii', 'replace').decode('ascii')}")
                    print(f"[OK] Confidence: {result.get('confidence', 0):.2f}")
                    print(f"[OK] Time: {end_time - start_time:.2f}s")
                    results[model] = result
                else:
                    print("[ERROR] Failed")
                    results[model] = None
                    
            except Exception as e:
                print(f"[ERROR] Error: {e}")
                results[model] = None
        
        return results
    
    def test_performance(self):
        """Test hiệu suất của hệ thống"""
        print(f"\n--- Performance Testing ---")
        
        # Test với text ngắn
        short_text = "Hello"
        print(f"\nShort text: '{short_text}'")
        start_time = time.time()
        result = self.manager.translate(short_text, 'en', 'vi')
        short_time = time.time() - start_time
        print(f"Time: {short_time:.3f}s")
        
        # Test với text dài
        long_text = "This is a very long text that will test the performance of our translation system. " * 10
        print(f"\nLong text: {len(long_text)} characters")
        start_time = time.time()
        result = self.manager.translate(long_text, 'en', 'vi')
        long_time = time.time() - start_time
        print(f"Time: {long_time:.3f}s")
        
        # Test với nhiều text
        print(f"\nMultiple texts (5 texts):")
        texts = ["Hello", "World", "Test", "Message", "Demo"]
        start_time = time.time()
        for text in texts:
            self.manager.translate(text, 'en', 'vi')
        batch_time = time.time() - start_time
        print(f"Total time: {batch_time:.3f}s")
        print(f"Average per text: {batch_time/len(texts):.3f}s")
    
    def test_language_pairs(self):
        """Test các cặp ngôn ngữ khác nhau"""
        print(f"\n--- Testing Language Pairs ---")
        
        test_pairs = [
            ('en', 'vi'), ('vi', 'en'),
            ('fr', 'vi'), ('vi', 'fr'),
            ('ja', 'vi'), ('vi', 'ja'),
            ('zh', 'vi'), ('vi', 'zh'),
            ('en', 'fr'), ('fr', 'en'),
            ('ja', 'zh'), ('zh', 'ja')
        ]
        
        test_text = "Hello world"
        
        for source, target in test_pairs:
            print(f"\n{source} -> {target}:")
            result = self.manager.translate(test_text, source, target)
            if result:
                print(f"[OK] '{result['text']}' (Model: {result.get('model_used', 'unknown')})")
            else:
                print("[ERROR] Failed")
    
    def test_error_handling(self):
        """Test xử lý lỗi"""
        print(f"\n--- Testing Error Handling ---")
        
        # Test với text rỗng
        print("\nEmpty text:")
        result = self.manager.translate("", 'en', 'vi')
        print(f"Result: {result}")
        
        # Test với text chỉ có số
        print("\nNumbers only:")
        result = self.manager.translate("123456", 'en', 'vi')
        if result:
            print(f"[OK] '{result['text']}'")
        else:
            print("[ERROR] Failed")
        
        # Test với text rất dài
        print("\nVery long text:")
        very_long_text = "A" * 10000
        start_time = time.time()
        result = self.manager.translate(very_long_text, 'en', 'vi')
        end_time = time.time()
        if result:
            print(f"[OK] Translated in {end_time - start_time:.2f}s")
        else:
            print("[ERROR] Failed")
    
    def get_model_comparison(self):
        """So sánh các mô hình"""
        print(f"\n--- Model Comparison ---")
        
        test_text = "Hello world, this is a test message for translation comparison."
        source_lang = 'en'
        target_lang = 'vi'
        
        print(f"Test text: '{test_text}'")
        print(f"Translation: {source_lang} -> {target_lang}")
        
        available_models = self.manager.get_available_models()
        comparison = {}
        
        for model in available_models:
            print(f"\n--- {model.upper()} ---")
            start_time = time.time()
            
            try:
                result = self.manager.translate_with_model(test_text, source_lang, target_lang, model)
                end_time = time.time()
                
                if result:
                    comparison[model] = {
                        'text': result['text'],
                        'confidence': result['confidence'],
                        'time': end_time - start_time,
                        'success': True
                    }
                    print(f"[OK] '{result['text']}'")
                    print(f"[OK] Confidence: {result.get('confidence', 0):.2f}")
                    print(f"[OK] Time: {end_time - start_time:.2f}s")
                else:
                    comparison[model] = {'success': False}
                    print("[ERROR] Failed")
                    
            except Exception as e:
                comparison[model] = {'success': False, 'error': str(e)}
                print(f"[ERROR] Error: {e}")
        
        return comparison
    
    def run_full_demo(self):
        """Chạy demo đầy đủ"""
        print("Starting full demo...")
        
        # 1. Test single translation
        self.test_single_translation("Hello world", 'en', 'vi')
        
        # 2. Test auto detection
        self.test_auto_detection()
        
        # 3. Test all models
        self.test_all_models("Hello world", 'en', 'vi')
        
        # 4. Test performance
        self.test_performance()
        
        # 5. Test language pairs
        self.test_language_pairs()
        
        # 6. Test error handling
        self.test_error_handling()
        
        # 7. Model comparison
        comparison = self.get_model_comparison()
        
        # 8. Summary
        self.print_summary(comparison)

    def run_quick_demo(self):
        """Chạy demo dịch nhanh với 5 cặp ngôn ngữ"""
        print("\n--- Quick Translation Demo ---")
        
        test_text = "Hello, how are you today?"
        language_pairs = [
            ('en', 'vi'), ('vi', 'en'),
            ('zh', 'en'), ('ja', 'en'), ('fr', 'en')
        ]
        
        for source_lang, target_lang in language_pairs:
            print(f"\nTranslating '{test_text}' from {source_lang} to {target_lang}:")
            available_models = self.manager.get_available_models()
            
            for model_name in available_models:
                try:
                    result = self.manager.translate_with_model(test_text, source_lang, target_lang, model_name)
                    if result and result['text']:
                        print(f"  {model_name}: '{result['text']}'")
                    else:
                        print(f"  {model_name}: [ERROR] Failed to translate")
                except Exception as e:
                    print(f"  {model_name}: [ERROR] {e}")

    def print_summary(self, comparison: Dict):
        """In tóm tắt kết quả"""
        print(f"\n=== SUMMARY ===")
        
        print(f"\nAvailable Models: {len(self.manager.get_available_models())}")
        for model in self.manager.get_available_models():
            model_info = self.manager.get_model_info(model)
            print(f"  - {model}: {model_info.get('provider', 'Unknown')} ({'Online' if not model_info.get('offline', True) else 'Offline'})")
        
        print(f"\nModel Performance Comparison:")
        for model, result in comparison.items():
            if result.get('success'):
                print(f"  - {model}: [OK] {result.get('confidence', 0):.2f} confidence, {result.get('time', 0):.2f}s")
            else:
                print(f"  - {model}: [ERROR] Failed")
        
        print(f"\nRecommendations:")
        if 'gemini' in comparison and comparison['gemini'].get('success'):
            print("  - Use Gemini for best quality (requires API key)")
        if 'nllb' in comparison and comparison['nllb'].get('success'):
            print("  - Use NLLB-200 for offline translation")
        if 'opus' in comparison and comparison['opus'].get('success'):
            print("  - Use OPUS-MT for lightweight translation")


def main():
    """Main function"""
    print("Translation System Demo")
    print("=" * 50)
    
    # Load config và kiểm tra API key
    config = TranslationConfig('config.env')
    api_key = config.get_api_key('gemini')
    
    if api_key:
        print(f"[OK] Gemini API key found: {api_key[:10]}...")
    else:
        print("[WARNING] Gemini API key not found")
        print("Please check config.env file")
        print("You can get a free API key from: https://makersuite.google.com/app/apikey")
        print("Continuing with offline models only...")
        print()
    
    try:
        demo = DemoTranslation()
        
        # Chọn loại test
        print("\nChoose test type:")
        print("1. Full demo (all tests)")
        print("2. Single translation test")
        print("3. Auto detection test")
        print("4. All models test")
        print("5. Performance test")
        print("6. Language pairs test")
        print("7. Error handling test")
        print("8. Model comparison")
        print("9. Quick translation demo")
        
        choice = input("\nEnter choice (1-9): ").strip()
        
        if choice == '1':
            demo.run_full_demo()
        elif choice == '2':
            text = input("Enter text to translate: ").strip()
            source = input("Enter source language (en/fr/ja/zh/vi): ").strip()
            target = input("Enter target language (en/fr/ja/zh/vi): ").strip()
            demo.test_single_translation(text, source, target)
        elif choice == '3':
            demo.test_auto_detection()
        elif choice == '4':
            text = input("Enter text to translate: ").strip()
            source = input("Enter source language (en/fr/ja/zh/vi): ").strip()
            target = input("Enter target language (en/fr/ja/zh/vi): ").strip()
            demo.test_all_models(text, source, target)
        elif choice == '5':
            demo.test_performance()
        elif choice == '6':
            demo.test_language_pairs()
        elif choice == '7':
            demo.test_error_handling()
        elif choice == '8':
            demo.get_model_comparison()
        elif choice == '9':
            demo.run_quick_demo()
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
