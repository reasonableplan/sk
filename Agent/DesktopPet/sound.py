import winsound
import threading

class SoundManager:
    """Windows 기본 사운드를 사용한 효과음 매니저"""
    
    def __init__(self):
        self.enabled = True
        
        # 주파수와 지속시간으로 정의된 효과음 (Hz, ms)
        self.sounds = {
            # 긍정적 이벤트
            "level_up": [(523, 100), (659, 100), (784, 150), (1047, 200)],  # C-E-G-C 팡파레
            "victory": [(659, 80), (784, 80), (880, 80), (1047, 200)],  # E-G-A-C 승리
            "purchase": [(880, 100), (1047, 150)],  # A-C 구매
            "heal": [(784, 100), (880, 100), (1047, 150)],  # G-A-C 회복
            
            # 중립적 이벤트
            "click": [(800, 50)],  # 클릭
            "notification": [(1000, 100), (800, 100)],  # 알림
            "chat": [(600, 80), (700, 80)],  # 대화
            
            # 부정적 이벤트
            "defeat": [(392, 150), (349, 150), (294, 200)],  # G-F-D 패배
            "error": [(200, 200)],  # 낮은 부저음
            "damage": [(400, 100)],  # 타격음
        }
    
    def play(self, sound_name):
        """효과음 재생 (비동기)"""
        if not self.enabled:
            return
        
        if sound_name not in self.sounds:
            print(f"[Sound] Unknown sound: {sound_name}")
            return
        
        # 별도 스레드에서 재생 (UI 블로킹 방지)
        thread = threading.Thread(target=self._play_sequence, args=(sound_name,))
        thread.daemon = True
        thread.start()
    
    def _play_sequence(self, sound_name):
        """음표 시퀀스 재생"""
        try:
            for freq, duration in self.sounds[sound_name]:
                winsound.Beep(freq, duration)
        except Exception as e:
            print(f"[Sound] Error playing {sound_name}: {e}")
    
    def toggle(self):
        """효과음 켜기/끄기"""
        self.enabled = not self.enabled
        return self.enabled
    
    def play_system_sound(self, sound_type):
        """Windows 시스템 사운드 재생"""
        if not self.enabled:
            return
        
        sound_map = {
            "asterisk": winsound.MB_ICONASTERISK,
            "exclamation": winsound.MB_ICONEXCLAMATION,
            "hand": winsound.MB_ICONHAND,
            "question": winsound.MB_ICONQUESTION,
            "ok": winsound.MB_OK,
        }
        
        if sound_type in sound_map:
            try:
                winsound.MessageBeep(sound_map[sound_type])
            except Exception as e:
                print(f"[Sound] Error playing system sound: {e}")
