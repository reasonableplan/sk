import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.multioutput import MultiOutputClassifier
from PyQt6.QtWidgets import QMessageBox

class LottoPredictor:
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.model = None
        self.is_trained = False

    def prepare_data(self, window_size=5):
        """
        과거 window_size 만큼의 회차 데이터를 Feature로,
        그 다음 회차 데이터를 Label로 사용하여 학습 데이터를 생성합니다.
        """
        if self.data_manager.df is None or len(self.data_manager.df) < window_size + 1:
            return None, None

        # 데이터 프레임 복사 및 정렬 (오래된 순)
        df = self.data_manager.df.sort_values(by='draw_no', ascending=True).copy()
        
        # 번호만 추출
        number_cols = [f'num{i}' for i in range(1, 7)]
        data = df[number_cols].values

        X = []
        y = []

        for i in range(len(data) - window_size):
            # 과거 n회차의 번호들을 1차원 배열로 펼침
            feature_vector = data[i : i + window_size].flatten()
            target_vector = data[i + window_size] # 다음 회차 번호
            
            X.append(feature_vector)
            
            # XGBoost MultiOutputClassifier를 위해
            # 타겟을 "다음 회차에 등장한 번호들의 집합 (One-hot)"으로 변환 (0 or 1)
            target_one_hot = np.zeros(45)
            for num in target_vector:
                target_one_hot[num-1] = 1 # 1-based index to 0-based
            y.append(target_one_hot)

        return np.array(X), np.array(y)

    def train(self):
        try:
            X, y = self.prepare_data()
            if X is None:
                return False

            # XGBClassifier 사용 (MultiOutputClassifier로 감싸서 다중 레이블 지원)
            # n_estimators: 부스팅 라운드 수
            xgb = XGBClassifier(
                n_estimators=100, 
                learning_rate=0.1, 
                max_depth=5, 
                random_state=42, 
                n_jobs=-1,
                eval_metric='logloss' # 경고 방지
            )
            # 45개의 이진 분류 문제로 변환하여 학습
            self.model = MultiOutputClassifier(xgb)
            self.model.fit(X, y)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"Training error: {e}")
            return False

    def predict(self, recent_data, top_n=6, exclude_numbers=None, include_numbers=None, noise_level=0.0):
        """
        recent_data: 가장 최근 window_size 만큼의 데이터 (2D array)
        noise_level: 예측 확률에 추가할 무작위 노이즈의 강도 (0.0 ~ 1.0). 세트마다 다양성을 주기 위해 사용.
        """
        if not self.is_trained:
            if not self.train():
                return []
        
        # 입력 데이터 shape 맞추기
        feature_vector = recent_data.flatten().reshape(1, -1)
        
        try:
            # MultiOutputClassifier의 predict_proba는 각 estimator별로 (n_samples, 2) 배열을 담은 리스트를 반환
            probs_list = self.model.predict_proba(feature_vector)
            
            # 확률 추출 (Dictionary: {번호: 확률})
            number_probs = {}
            for i, probs in enumerate(probs_list):
                # probs has shape (1, 2) -> [prob_0, prob_1]
                # 우리가 원하는 것은 1(나올 확률)
                # 만약 클래스가 하나뿐이라면 (예: 데이터셋에서 한 번도 안 나온 번호) shape는 (1, 1)이 될 수 있음
                prob_appearing = 0.0
                if probs.shape[1] == 2:
                    prob_appearing = probs[0][1]
                elif probs.shape[1] == 1:
                    # 해당 클래스가 0인지 1인지 확인 필요하지만
                    # XGBoost 특성상 보통 0/1 둘 다 없으면 에러 혹은 하나만 있음.
                    # MultiOutputClassifier의 내부 estimator.classes_ 확인
                    estimator = self.model.estimators_[i]
                    if 1 in estimator.classes_:
                         prob_appearing = probs[0][0] # 유일한 클래스가 1이면 확률 1.0 (거의 없을 듯)
                    else:
                         prob_appearing = 0.0 # 유일한 클래스가 0이면 확률 0.0
                
                # 가중치 다양화를 위한 노이즈 주입
                if noise_level > 0:
                    # -noise_level ~ +noise_level 사이의 랜덤 값 더하기
                    noise = np.random.uniform(-noise_level, noise_level)
                    prob_appearing += noise
                    # 확률 범위 0~1 클리핑 하지 않음 (상대적 크기만 중요하므로, 음수만 처리)
                
                if prob_appearing < 0:
                    prob_appearing = 0.0001 # 0 이하 방지

                number_probs[i + 1] = prob_appearing

            # 1. 포함할 번호 처리
            picked = []
            if include_numbers:
                picked.extend(include_numbers)
            
            # 2. 후보군 및 가중치 준비
            candidates = []
            weights = []
            
            for num, prob in number_probs.items():
                # 제외 번호이거나 이미 포함된 번호는 건너뜀
                if (exclude_numbers and num in exclude_numbers) or (num in picked):
                    continue
                
                candidates.append(num)
                weights.append(prob)
            
            # 남은 뽑아야 할 개수
            remaining_count = top_n - len(picked)
            
            if remaining_count > 0:
                # 가중치 합이 0이면 균등 확률로 설정 (에러 방지)
                if sum(weights) == 0:
                    weights = [1.0] * len(weights)
                
                weights = np.array(weights)
                weights = weights / weights.sum() # 정규화
                
                # 가중치 기반 랜덤 비복원 추출
                chosen_randomly = np.random.choice(
                    candidates, 
                    size=remaining_count, 
                    replace=False, 
                    p=weights
                )
                picked.extend(chosen_randomly)
            
            return sorted(picked)

        except Exception as e:
            print(f"Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return []
