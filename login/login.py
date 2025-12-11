import streamlit as st
import sqlite3
import bcrypt
import re

# --- 데이터베이스 설정 ---
DATABASE_NAME = "booking.db"

def init_db():
    """데이터베이스 및 users 테이블 초기화"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            phone_number TEXT UNIQUE NOT NULL,
            secret_answer TEXT NOT NULL,
            hint TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_user(username, hashed_password, name, phone_number, hashed_secret_answer, hint):
    """새로운 사용자 추가. 성공 여부와 오류 메시지를 반환."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password, name, phone_number, secret_answer, hint) VALUES (?, ?, ?, ?, ?, ?)",
            (username, hashed_password, name, phone_number, hashed_secret_answer, hint)
        )
        conn.commit()
        return True, None # 성공 시 True와 None 반환
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return False, "이미 존재하는 아이디입니다. 다른 아이디를 선택해주세요."
        elif "phone_number" in str(e):
            return False, "이미 등록된 전화번호입니다. 다른 전화번호를 사용해주세요."
        else:
            return False, "회원가입 중 고유성 제약 조건 오류가 발생했습니다: " + str(e)
    except Exception as e:
        return False, f"회원가입 중 알 수 없는 오류가 발생했습니다: {e}"
    finally:
        conn.close()

def get_user_by_username(username):
    """아이디로 사용자 정보 조회"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_name_phone(name, phone_number):
    """이름과 전화번호로 사용자 정보 조회 (아이디 찾기용)"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE name=? AND phone_number=?", (name, phone_number))
    user_data = cursor.fetchone()
    conn.close()
    return user_data

def update_password(username, new_hashed_password):
    """사용자의 비밀번호 업데이트"""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password=? WHERE username=?", (new_hashed_password, username))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"비밀번호 업데이트 중 오류가 발생했습니다: {e}")
        return False
    finally:
        conn.close()

# --- 정규 표현식 및 유효성 검사 ---
USERNAME_REGEX = r"^[a-zA-Z0-9.@]+$" # 아이디: 대소문자, 숫자, 특수문자 . @ 만 허용 (공백 불가)
PASSWORD_REGEX = r"^[a-zA-Z0-9]+$"   # 비밀번호: 대소문자, 숫자만 허용 (최소 길이 8자, 공백 불가)
PASSWORD_MIN_LENGTH = 8
PHONE_NUMBER_REGEX = r"^\d{10,11}$"  # 전화번호: 숫자만 허용 (10~11자리 숫자)

def validate_username(username):
    if not username: return "아이디를 입력해주세요."
    if not re.match(USERNAME_REGEX, username):
        return "아이디는 대소문자, 숫자, '.', '@' 만 포함할 수 있습니다. (공백 불가)"
    return None

def validate_password(password):
    if not password: return "비밀번호를 입력해주세요."
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"비밀번호는 최소 {PASSWORD_MIN_LENGTH}자리 이상이어야 합니다."
    if not re.match(PASSWORD_REGEX, password):
        return "비밀번호는 대소문자와 숫자만 포함할 수 있습니다. (공백 불가)"
    return None

def validate_name(name):
    if not name: return "이름을 입력해주세요."
    return None

def validate_phone_number(phone_number):
    if not phone_number: return "전화번호를 입력해주세요."
    if not re.match(PHONE_NUMBER_REGEX, phone_number):
        return "유효한 전화번호 형식(숫자만 10~11자리)으로 입력해주세요."
    return None

def validate_secret_answer(answer):
    if not answer: return "비밀 단어/문장을 입력해주세요."
    return None

def validate_hint(hint):
    if not hint: return "힌트를 입력해주세요."
    return None

# --- 비밀번호 및 비밀 단어/문장 암호화 함수 ---
def hash_text(text):
    """텍스트를 bcrypt로 해시화 (비밀번호, 비밀 단어/문장)"""
    hashed = bcrypt.hashpw(text.encode('utf-8'), bcrypt.gensalt())
    return hashed.decode('utf-8')

def check_hashed_text(plain_text, hashed_text):
    """평문 텍스트와 해시된 텍스트 비교"""
    return bcrypt.checkpw(plain_text.encode('utf-8'), hashed_text.encode('utf-8'))

# --- 폼 입력 초기화 헬퍼 함수 ---
def clear_registration_form_fields_and_flags():
    """회원가입 폼 필드 및 관련 내부 플래그 (중복확인 등) 초기화"""
    for key_suffix in ['reg_username', 'reg_name_form', 'reg_phone_form',
                       'reg_password_form', 'reg_confirm_password_form',
                       'reg_secret_answer_form', 'reg_hint_form']:
        if key_suffix in st.session_state:
            del st.session_state[key_suffix]

    st.session_state.username_available = False
    st.session_state.last_checked_username = ""
    st.session_state.show_inline_success_message = False
    st.session_state.username_check_error = ""

def clear_login_form():
    if 'login_username_input_form' in st.session_state: del st.session_state.login_username_input_form
    if 'login_password_input_form' in st.session_state: del st.session_state.login_password_input_form

def clear_find_id_form():
    if 'find_id_name_form' in st.session_state: del st.session_state.find_id_name_form
    if 'find_id_phone_form' in st.session_state: del st.session_state.find_id_phone_form

def clear_find_pw_form():
    for key_suffix in ['forgot_pw_username_step1_form', 'forgot_pw_secret_input_form',
                       'forgot_pw_new_input_form', 'forgot_pw_confirm_new_input_form']:
        if key_suffix in st.session_state:
            del st.session_state[key_suffix]
    st.session_state.forgot_pw_step = 1
    for key in ['forgot_pw_username', 'forgot_pw_hint', 'stored_secret_answer_hash']:
        if key in st.session_state:
            del st.session_state[key]


# on_change 콜백 함수
def on_page_change():
    """페이지 변경 시 이전 페이지 폼 필드 초기화"""
    # st.session_state.current_page is already updated by st.radio before on_change is called
    # st.session_state.last_selected_page holds the value *before* the change.

    # Clear the form of the page that was *just left*
    if st.session_state.last_selected_page == "회원가입":
        clear_registration_form_fields_and_flags()
        # registration_success_message_display는 로그인 페이지로 넘겨주기 위해 여기서 지우지 않음.
        # 로그인 페이지에서 메시지를 표시한 후 스스로 지우도록 처리
    elif st.session_state.last_selected_page == "로그인":
        clear_login_form()
    elif st.session_state.last_selected_page == "아이디 찾기":
        clear_find_id_form()
    elif st.session_state.last_selected_page == "비밀번호 찾기":
        clear_find_pw_form()

    # Now, update last_selected_page to the *new* current page for the next run
    st.session_state.last_selected_page = st.session_state.current_page


# --- Streamlit 앱 본문 ---
st.set_page_config(page_title="범용 예약 시스템", layout="centered")

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'forgot_pw_step' not in st.session_state:
    st.session_state.forgot_pw_step = 1
if 'username_available' not in st.session_state:
    st.session_state.username_available = False
if 'last_checked_username' not in st.session_state:
    st.session_state.last_checked_username = ""
if 'show_inline_success_message' not in st.session_state:
    st.session_state.show_inline_success_message = False
if 'username_check_error' not in st.session_state:
    st.session_state.username_check_error = ""

if 'current_page' not in st.session_state:
    st.session_state.current_page = "로그인"
if 'last_selected_page' not in st.session_state:
    st.session_state.last_selected_page = "로그인"

# New session state for registration success message
if 'registration_success_message_display' not in st.session_state:
    st.session_state.registration_success_message_display = None


init_db() # 앱 시작 시 데이터베이스 초기화

st.title("🌐 범용 예약 시스템")

# --- 로그인 성공 시 메인 페이지 ---
if st.session_state.logged_in:
    st.success(f"{st.session_state.username}님, 환영합니다!")
    st.write("여기는 예약 시스템의 메인 페이지입니다. 호텔, 항공 등 다양한 예약 기능을 여기에 추가할 수 있습니다.")

    if st.button("로그아웃"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.forgot_pw_step = 1
        clear_login_form() # Clear login form fields upon logout
        st.rerun()

# --- 로그인되지 않은 경우 (로그인/회원가입/아이디 찾기/비밀번호 찾기) ---
else:
    page_options = ["로그인", "회원가입", "아이디 찾기", "비밀번호 찾기"]
    default_index = page_options.index(st.session_state.current_page) if st.session_state.current_page in page_options else 0

    st.session_state.current_page = st.radio(
        "메뉴",
        page_options,
        key="main_navigation_radio",
        index=default_index,
        on_change=on_page_change,
        horizontal=True
    )

    if st.session_state.current_page == "로그인":
        st.header("로그인")

        # 회원가입 성공 메시지를 로그인 페이지에서 표시
        if st.session_state.registration_success_message_display:
            st.success(st.session_state.registration_success_message_display)
            st.session_state.registration_success_message_display = None # 메시지를 한 번 표시한 후 삭제

        with st.form(key="login_form"):
            login_username = st.text_input("아이디", key="login_username_input_form", value=st.session_state.get('login_username_input_form', ''))
            login_password = st.text_input("비밀번호", type="password", key="login_password_input_form", value=st.session_state.get('login_password_input_form', ''))

            submitted = st.form_submit_button("로그인")

            if submitted:
                user = get_user_by_username(login_username)
                if user:
                    if check_hashed_text(login_password, user[2]):
                        st.session_state.logged_in = True
                        st.session_state.username = login_username
                        st.success("로그인 성공!")
                        st.rerun() # Rerun to switch to main content
                    else:
                        st.error("비밀번호가 올바르지 않습니다.")
                else:
                    st.error("존재하지 않는 아이디입니다.")

    elif st.session_state.current_page == "회원가입":
        st.header("회원가입")

        # 회원가입 성공 메시지는 이제 로그인 페이지에서만 표시되므로, 여기서는 별도의 메시지 표시를 제거합니다.
        # 사용자가 수동으로 '회원가입' 탭을 선택했을 때만 이 메시지가 표시될 수 있습니다.
        if st.session_state.registration_success_message_display:
            st.info("회원가입이 완료되었습니다. 로그인 페이지로 이동하여 로그인해주세요.")
            # 이 메시지는 사용자가 '회원가입' 탭에 남아있을 때만 일시적으로 보이고,
            # 자동으로 로그인 페이지로 이동하기 때문에 이 코드가 실행될 일은 거의 없습니다.
            # 하지만 혹시 모를 상황을 위해 넣어두었습니다.


        with st.form(key="check_username_form", clear_on_submit=False):
            col1, col2 = st.columns([0.7, 0.3])

            with col1:
                new_username = st.text_input("새 아이디", key="reg_username",
                                            value=st.session_state.get('reg_username', ''),
                                            placeholder="아이디를 입력해주세요.")
            with col2:
                st.write("") # For vertical alignment
                submitted_check_username = st.form_submit_button("중복 확인", key="check_username_duplication_button")

            # Reset availability flags if username input changes *from the last successfully checked one*
            if new_username != st.session_state.get('last_checked_username', ''):
                st.session_state.username_available = False
                st.session_state.show_inline_success_message = False
                st.session_state.username_check_error = "" # Clear error when username changes

            if submitted_check_username:
                username_error = validate_username(new_username)
                if username_error:
                    st.session_state.username_check_error = username_error
                    st.session_state.username_available = False
                    st.session_state.last_checked_username = "" # Reset last checked username on failure
                    st.session_state.show_inline_success_message = False
                else:
                    user_exists = get_user_by_username(new_username)
                    if user_exists:
                        st.session_state.username_check_error = f"아이디 '{new_username}'은(는) 이미 사용 중입니다."
                        st.session_state.username_available = False
                        st.session_state.last_checked_username = "" # Reset last checked username on failure
                        st.session_state.show_inline_success_message = False
                    else:
                        st.session_state.username_check_error = "" # Clear previous error if check is successful
                        st.session_state.username_available = True
                        st.session_state.last_checked_username = new_username # Only set last_checked_username on success
                        st.session_state.show_inline_success_message = True
                st.rerun() # Rerun to display messages and potentially update form state

            # --- Status messages for username check ---
            if st.session_state.get('username_check_error'):
                st.error(st.session_state.username_check_error)
            elif st.session_state.get('show_inline_success_message', False) and \
                 st.session_state.get('username_available', False) and \
                 st.session_state.get('last_checked_username') == new_username:
                st.success(f"아이디 '{new_username}'은(는) 사용 가능합니다.")
                st.info("회원가입을 진행할 수 있습니다.") # Additional guidance
            elif not new_username: # No input yet
                st.info("사용할 아이디를 입력하고 중복 확인을 해주세요.")
            elif not st.session_state.get('username_available', False) or \
                 st.session_state.get('last_checked_username') != new_username:
                # This covers cases where username was checked and found duplicate/invalid,
                # or username was changed after a successful check, or not checked yet.
                st.warning("아이디 중복 확인이 필요합니다. 아이디를 변경했다면 다시 중복 확인해주세요.")


        with st.form(key="register_form"):
            reg_name = st.text_input("이름", key="reg_name_form", value=st.session_state.get('reg_name_form', ''))
            reg_phone_number = st.text_input("전화번호 (숫자만)", key="reg_phone_form", value=st.session_state.get('reg_phone_form', ''), placeholder="예: 01012345678")
            reg_password = st.text_input("새 비밀번호", type="password", key="reg_password_form", value=st.session_state.get('reg_password_form', ''))
            reg_confirm_password = st.text_input("비밀번호 확인", type="password", key="reg_confirm_password_form", value=st.session_state.get('reg_confirm_password_form', ''))
            reg_secret_answer = st.text_input("비밀 단어/문장 (비밀번호 재설정 시 사용됩니다)", type="password", key="reg_secret_answer_form", value=st.session_state.get('reg_secret_answer_form', ''))
            reg_hint = st.text_input("비밀 단어/문장 힌트", key="reg_hint_form", value=st.session_state.get('reg_hint_form', ''))
            st.caption("💡 힌트는 비밀 단어/문장을 기억하는 데 도움이 되는 정보입니다. 직접적인 답변을 적거나 너무 유추하기 쉬운 정보는 피해주세요. 이 힌트가 유출될 경우 비밀 단어/문장도 노출될 위험이 있습니다.")

            submitted_reg = st.form_submit_button("회원가입")

            if submitted_reg:
                registration_pre_errors = []

                final_username_for_reg = st.session_state.get('last_checked_username')

                if not st.session_state.get('username_available') or final_username_for_reg != new_username:
                    registration_pre_errors.append("아이디 중복 확인을 완료하거나, 확인된 아이디를 변경하지 않았는지 확인해주세요.")
                elif not final_username_for_reg:
                     registration_pre_errors.append("아이디를 입력하고 중복 확인을 완료해주세요.")


                if registration_pre_errors:
                    st.error("회원가입 실패:\n" + "\n".join(registration_pre_errors))
                else:
                    validation_errors = []

                    name_error = validate_name(reg_name)
                    if name_error: validation_errors.append(name_error)
                    phone_error = validate_phone_number(reg_phone_number)
                    if phone_error: validation_errors.append(phone_error)
                    password_error = validate_password(reg_password)
                    if password_error: validation_errors.append(password_error)
                    secret_answer_error = validate_secret_answer(reg_secret_answer)
                    if secret_answer_error: validation_errors.append(secret_answer_error)
                    hint_error = validate_hint(reg_hint)
                    if hint_error: validation_errors.append(hint_error)


                    if reg_password != reg_confirm_password:
                        validation_errors.append("비밀번호가 일치하지 않습니다.")

                    if validation_errors:
                        st.error("회원가입 실패. 다음 오류들을 해결해주세요:\n" + "\n".join(validation_errors))
                    else:
                        hashed_pw = hash_text(reg_password)
                        hashed_secret_ans = hash_text(reg_secret_answer)

                        success, error_message = add_user(final_username_for_reg, hashed_pw, reg_name, reg_phone_number, hashed_secret_ans, reg_hint)
                        if success:
                            st.session_state.registration_success_message_display = "회원가입에 성공했습니다. 로그인 페이지에서 로그인해주세요."
                            clear_registration_form_fields_and_flags() # Clear all registration form inputs and flags
                            st.session_state.current_page = "로그인" # Automatically navigate to login page
                            st.session_state.last_selected_page = "회원가입" # For on_page_change to clear reg form on next run
                            st.rerun() # Rerun to switch to login page and display message
                        else:
                            st.error(f"회원가입 실패: {error_message}")


    elif st.session_state.current_page == "아이디 찾기":
        st.header("아이디 찾기")
        with st.form(key="find_id_form"):
            find_id_name = st.text_input("이름", key="find_id_name_form", value=st.session_state.get('find_id_name_form', ''))
            find_id_phone = st.text_input("전화번호 (숫자만)", key="find_id_phone_form", value=st.session_state.get('find_id_phone_form', ''), placeholder="예: 01012345678")

            submitted_find_id = st.form_submit_button("아이디 찾기")

            if submitted_find_id:
                name_error = validate_name(find_id_name)
                phone_error = validate_phone_number(find_id_phone)

                if name_error: st.error(name_error)
                if phone_error: st.error(phone_error)

                if not name_error and not phone_error:
                    user_data = get_user_by_name_phone(find_id_name, find_id_phone)
                    if user_data:
                        st.success(f"찾으시는 아이디는: **{user_data[0]}** 입니다.")
                    else:
                        st.error("일치하는 사용자 정보가 없습니다.")

    elif st.session_state.current_page == "비밀번호 찾기":
        st.header("비밀번호 찾기 (재설정)")

        if st.session_state.forgot_pw_step == 1:
            st.subheader("1단계: 아이디 입력")
            with st.form(key="forgot_pw_step1_form"):
                forgot_pw_username = st.text_input("아이디를 입력해주세요.", key="forgot_pw_username_step1_form", value=st.session_state.get('forgot_pw_username_step1_form', ''))
                submitted_step1 = st.form_submit_button("힌트 확인")

                if submitted_step1:
                    user = get_user_by_username(forgot_pw_username)
                    if user:
                        st.session_state.forgot_pw_username = forgot_pw_username
                        st.session_state.forgot_pw_hint = user[6]
                        st.session_state.stored_secret_answer_hash = user[5]
                        st.session_state.forgot_pw_step = 2
                        st.success(f"아이디 **{forgot_pw_username}** 의 힌트가 확인되었습니다. 다음 단계로 진행해주세요.")
                        st.rerun()
                    else:
                        st.error("존재하지 않는 아이디입니다.")

        elif st.session_state.forgot_pw_step == 2:
            st.subheader("2단계: 비밀 단어/문장 입력 및 새 비밀번호 설정")
            st.info(f"아이디: **{st.session_state.forgot_pw_username}**")
            st.info(f"힌트: **{st.session_state.forgot_pw_hint}**")

            with st.form(key="forgot_pw_step2_form"):
                entered_secret_answer = st.text_input("비밀 단어/문장을 입력해주세요.", type="password", key="forgot_pw_secret_input_form", value=st.session_state.get('forgot_pw_secret_input_form', ''))
                new_pw = st.text_input("새 비밀번호", type="password", key="forgot_pw_new_input_form", value=st.session_state.get('forgot_pw_new_input_form', ''))
                confirm_new_pw = st.text_input("새 비밀번호 확인", type="password", key="forgot_pw_confirm_new_input_form", value=st.session_state.get('forgot_pw_confirm_new_input_form', ''))

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submitted_step2 = st.form_submit_button("비밀번호 재설정")
                with col_btn2:
                    if st.form_submit_button("이전 단계로 돌아가기", key="btn_forgot_pw_back_form_submit"):
                        st.session_state.forgot_pw_step = 1
                        clear_find_pw_form() # Clear form fields specific to step 2 when going back
                        st.rerun()

                if submitted_step2:
                    validation_errors_pw_reset = []

                    secret_ans_error = validate_secret_answer(entered_secret_answer)
                    if secret_ans_error: validation_errors_pw_reset.append(secret_ans_error)

                    new_pw_error = validate_password(new_pw)
                    if new_pw_error: validation_errors_pw_reset.append(new_pw_error)

                    if new_pw != confirm_new_pw:
                        validation_errors_pw_reset.append("새 비밀번호가 일치하지 않습니다.")

                    if validation_errors_pw_reset:
                        st.error("다음 오류들을 해결해주세요:\n" + "\n".join(validation_errors_pw_reset))
                    else:
                        if check_hashed_text(entered_secret_answer, st.session_state.stored_secret_answer_hash):
                            hashed_new_pw = hash_text(new_pw)
                            if update_password(st.session_state.forgot_pw_username, hashed_new_pw):
                                st.success("비밀번호가 성공적으로 재설정되었습니다! 새 비밀번호로 로그인해주세요.")
                                st.session_state.forgot_pw_step = 1
                                clear_find_pw_form() # Clear all related form fields
                                st.session_state.current_page = "로그인" # Navigate to login page
                                st.session_state.last_selected_page = "비밀번호 찾기" # Simulate leaving this page
                                st.rerun()
                            else:
                                pass # Error message already shown by update_password function
                        else:
                            st.error("비밀 단어/문장이 일치하지 않습니다. 다시 시도해주세요.")
