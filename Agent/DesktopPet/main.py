import sys
from PyQt6.QtWidgets import QApplication, QMenu, QMessageBox
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QTimer
from pet_core import PetState
from pet_ui import PetUI

from tutor import EnglishTutor
from posture import PostureGuard
from menu import MenuMaster
from dungeon import DungeonGame
from dungeon import DungeonGame
from chat import PetChat
from crawler import SmartCrawler
from shop import ItemShop
from sound import SoundManager
from assistant import AIAssistant
from coding_assistant import EnhancedCodingAssistant

def main():
    # 전역 예외 처리기 (크래시 디버깅용)
    def exception_hook(exctype, value, traceback):
        import traceback as tb
        error_msg = "".join(tb.format_exception(exctype, value, traceback))
        print(error_msg) # 콘솔 출력
        
        # UI가 있다면 메시지 박스로도 표시
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("치명적인 오류 발생")
        msg.setText("오류가 발생하여 프로그램이 종료됩니다.")
        msg.setDetailedText(error_msg)
        msg.exec()
        sys.exit(1)

    sys.excepthook = exception_hook

    app = QApplication(sys.argv)
    # 툴 윈도우(PetUI)만 떠 있을 때도 종료되지 않도록 설정
    app.setQuitOnLastWindowClosed(False) 
    
    # Core State 초기화
    state = PetState()
    
    # UI 초기화
    ui = PetUI(state)
    ui.show()

    # Modules
    tutor = EnglishTutor()
    # 30분(실제로는 30초)마다 알림
    posture_guard = PostureGuard(interval_minutes=30) 
    menu_master = MenuMaster()
    dungeon = DungeonGame(state)
    chat = PetChat(state)
    shop = ItemShop(state)
    sound = SoundManager()
    assistant = AIAssistant()
    coding_assistant = EnhancedCodingAssistant()

    # Connect Signals
    def on_quiz_finished(success, int_gain):
        if success:
            state.study(int_gain)
            sound.play("notification")
            ui.bubble_label.setText("똑똑해진 기분이야! (+지능)")
        else:
            state.mood -= 5
            sound.play("error")
            ui.bubble_label.setText("아쉽다... 다음에 잘하자.")
        ui.update_stats()

    tutor.quiz_finished.connect(on_quiz_finished)

    def on_rest_finished(hp_gain):
        if hp_gain > 0:
            state.exercise(hp_gain)
            sound.play("heal")
            ui.bubble_label.setText("으라차차! 개운하다! (+체력)")
            ui.set_action("stretch", 3000) # 3초간 스트레칭 동작
        else:
            state.health = max(0, state.health + hp_gain) # hp_gain is negative
            state.mood -= 10
            sound.play("damage")
            ui.bubble_label.setText("으으... 몸이 뻐근해.")
        ui.update_stats()

    posture_guard.rest_finished.connect(on_rest_finished)

    def on_feed_finished(name, mood, health, hunger):
        state.feed(hunger)
        state.mood += mood
        state.health += health
        sound.play("notification")
        
        ui.bubble_label.setText(f"{name} 맛있어! ❤️")
        ui.update_stats()
    
    menu_master.feed_finished.connect(on_feed_finished)

    def on_battle_finished(win, gold):
        if win:
            old_level = state.level
            state.gold += gold
            state.gain_exp(50) # 경험치 대량 획득
            if state.level > old_level:  # Level up occurred
                sound.play("level_up")
            state.mood += 20
            sound.play("victory")
            ui.bubble_label.setText(f"승리했다! ({gold}G 획득) 👑")
        else:
            state.mood -= 30
            state.health = 1 # 기절했으니 피 1
            sound.play("defeat")
            ui.bubble_label.setText("패배했어... 분하다...")
        
        ui.set_equip(None) # 칼 집어넣기
        ui.update_stats()

    dungeon.battle_finished.connect(on_battle_finished)

    def on_item_purchased(item_type, value):
        sound.play("purchase")
        # Check for level up from exp booster
        if item_type == "exp":
            sound.play("level_up")
    
    shop.item_purchased.connect(on_item_purchased)

    def on_chat_command(command):
        if command == "open_menu":
            menu_master.show()
        elif command == "weather":
            ui.bubble_label.setText(crawler.get_weather())
        elif command == "news_eco":
             show_info(crawler.get_news("경제"))
        elif command == "exchange":
            ui.bubble_label.setText(crawler.get_exchange_rate())
            
    chat.command_triggered.connect(on_chat_command)

    def on_task_reminder(message):
        ui.bubble_label.setText(message)
        sound.play("notification")
    
    def on_break_reminder():
        ui.bubble_label.setText("1시간 동안 집중했어요! 잠깐 쉬어가요 ☕")
        sound.play("notification")
        posture_guard.alert_posture()  # 자세 교정 알림도 함께
    
    assistant.task_reminder.connect(on_task_reminder)
    assistant.break_reminder.connect(on_break_reminder)

    def on_coding_reminder(message):
        ui.bubble_label.setText(message)
        sound.play("notification")
    
    coding_assistant.reminder_signal.connect(on_coding_reminder)

    # --- Smart Agent Setup (Timer) ---
    crawler = SmartCrawler()

    def show_info(text):
        if len(text) > 80:
             # 말풍선에 맞게 줄임
            ui.bubble_label.setText(text[:80] + "...")
        else:
            ui.bubble_label.setText(text)

    # 30초마다 30% 확률로 정보 말하기
    info_timer = QTimer(ui)
    
    def auto_smart_speech():
        import random
        
        if random.random() < 0.3:  # 30% 확률로 정보 말하기
            info_options = [
                crawler.get_weather(),
                crawler.get_news("경제"),
                crawler.get_news("과학"),
                crawler.get_exchange_rate(),
                assistant.get_summary()  # 비서 요약 추가
            ]
            text = random.choice(info_options)
            
            if len(text) > 80:
                ui.bubble_label.setText(text[:80] + "...")
            else:
                ui.bubble_label.setText(text)
            
    info_timer.timeout.connect(auto_smart_speech)
    info_timer.start(30000) # 30초 주기

    # 트레이 아이콘이나 우클릭 메뉴 추가 가능
    def show_context_menu(pos):
        menu = QMenu()
        
        # 메뉴 구성
        menu.addSection("정보")
        
        info_action = QAction("📊 내 정보 (Status)", ui)
        def show_status_window():
            msg = QMessageBox(ui)
            msg.setWindowTitle("Pet Status")
            s = state
            info_text = f"""
            <h2>[ {s.name} ]</h2>
            <p><b>Lv.{s.level}</b> ({s.character_type})</p>
            <p>던전 진행: <b>Stage {s.dungeon_stage}</b></p>
            <hr>
            <p>❤️ 체력: {int(s.health)} / {int(s.max_health)}</p>
            <p>💧 마나: {int(s.mana)} / {int(s.max_mana)}</p>
            <p>😋 배고픔: {int(s.hunger)} %</p>
            <p>🙂 기분: {int(s.mood)} %</p>
            <hr>
            <p>⚔️ 공격력: {int(s.attack)}</p>
            <p>🛡️ 방어력: {int(s.defense)}</p>
            <p>⚡ 회피율: {s.evasion:.1f} %</p>
            <p>🧠 지능: {int(s.intellect)}</p>
            <hr>
            <p>💰 골드: {s.gold} G</p>
            """
            msg.setText(info_text)
            msg.exec()
            
        info_action.triggered.connect(show_status_window)
        menu.addAction(info_action)


        menu.addSection("활동")
        
        # 기능 실행
        chat_action = QAction("💬 펫과 대화하기", ui)
        chat_action.triggered.connect(chat.show)
        menu.addAction(chat_action)

        quiz_action = QAction("영어 퀴즈 풀기 (지능Up)", ui)
        quiz_action.triggered.connect(tutor.new_quiz)
        menu.addAction(quiz_action)
        
        posture_action = QAction("자세 교정 알림 테스트", ui)
        posture_action.triggered.connect(posture_guard.alert_posture)
        menu.addAction(posture_action)

        food_action = QAction("밥 먹자 (메뉴 추천/주기)", ui)
        food_action.triggered.connect(menu_master.show)
        menu.addAction(food_action)

        dungeon_action = QAction("⚔️ 미니 던전 입장", ui)
        
        def start_dungeon_mode():
            ui.set_equip("sword")
            ui.bubble_label.setText("전투 준비 완료! (비장)")
            dungeon.start_battle()

        dungeon_action.triggered.connect(start_dungeon_mode)
        menu.addAction(dungeon_action)

        shop_action = QAction("🛒 아이템 상점", ui)
        shop_action.triggered.connect(shop.show)
        menu.addAction(shop_action)

        assistant_action = QAction("🤖 AI 비서 대시보드", ui)
        assistant_action.triggered.connect(assistant.show)
        menu.addAction(assistant_action)

        coding_action = QAction("💻 코딩 비서", ui)
        coding_action.triggered.connect(coding_assistant.show)
        menu.addAction(coding_action)

        # 캐릭터 변경 메뉴
        char_menu = menu.addMenu("🎭 캐릭터 변경")
        
        # 현재 레벨/단계에 맞는 이름 미리 계산
        current_stage = state.evolution_stage
        
        # (타입키, 1단계이름, 2단계이름, 3단계이름)
        type_info = [
            ("default", "감자", "감자 전사", "제왕 감자"),
            ("slime",   "슬라임", "메가 슬라임", "슬라임 킹"),
            ("rock",    "조약돌", "골렘", "마그마 타이탄"),
            ("dog",     "강아지", "늑대", "푸른 불꽃 펜릴"),
            ("ghost",   "유령", "팬텀", "죽음의 리퍼"),
            ("robot",   "로봇", "안드로이드", "메카 워로드"),
            ("cloud",   "구름", "먹구름", "폭풍의 정령"),
            ("egg",     "알", "해츨링", "드래곤 로드")
        ]
        
        def make_change_handler(c_type, c_name):
            def handler():
                state.character_type = c_type
                ui.update() # 즉시 리페인팅
                ui.bubble_label.setText(f"변신! ({c_name})")
            return handler

        for t_key, name1, name2, name3 in type_info:
            display_name = name1
            if current_stage == 2: display_name = name2
            elif current_stage == 3: display_name = name3
            
            # 현재 선택된 캐릭터 체크 표시? (QAction setCheckable 등 가능하지만 일단 이름만)
            action = QAction(display_name, ui)
            action.triggered.connect(make_change_handler(t_key, display_name))
            char_menu.addAction(action)

        menu.addSeparator()
        debug_menu = menu.addMenu("🛠️ 개발자 도구")
        
        def set_level(lv):
            print(f"[Debug] Setting Level to {lv}...")
            state.level = lv
            state.sync_evolution_stage()
            print(f"[Debug] New Stage: {state.evolution_stage}")
            state.recalc_stats()
            state.save_state() # Force save
            ui.update()
            ui.repaint() # Force immediate repaint
            ui.bubble_label.setText(f"레벨 {lv} 설정 (진화 {state.evolution_stage}단계)")

        lv20_action = QAction("🚀 Lv.20 (3차 진화)", ui)
        lv20_action.triggered.connect(lambda: set_level(20))
        debug_menu.addAction(lv20_action)

        lv10_action = QAction("⬆️ Lv.10 (2차 진화)", ui)
        lv10_action.triggered.connect(lambda: set_level(10))
        debug_menu.addAction(lv10_action)

        reset_action = QAction("🔄 Lv.1 (초기화)", ui)
        reset_action.triggered.connect(lambda: set_level(1))
        debug_menu.addAction(reset_action)

        quit_action = QAction("종료", ui)
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)

        menu.exec(ui.mapToGlobal(pos))

    # CustomContextMenu
    ui.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) 
    ui.customContextMenuRequested.connect(show_context_menu)

    # 종료 시 자동 저장
    app.aboutToQuit.connect(state.save_state)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
