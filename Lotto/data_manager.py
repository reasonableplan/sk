import sys
import pandas as pd
import random
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt # Added for DateFormat

class LottoDataManager:
    def __init__(self, csv_path='로또.csv'):
        self.csv_path = csv_path
        self.df = None
        self.all_numbers_flat = [] # 1~45, 보너스 포함 모든 당첨 번호 (빈도 분석용)
        self.max_draw_no = 0
        self._load_data()

    def _load_data(self):
        try:
            # CSV 파일 로드
            # '회차', '날짜', '1', '2', '3', '4', '5', '6', '보너스'
            self.df = pd.read_csv(self.csv_path)

            # 컬럼명 정리 및 타입 변환
            self.df.columns = ['draw_no', 'draw_date', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6', 'bonus_num']
            self.df['draw_date'] = pd.to_datetime(self.df['draw_date'])
            self.df['draw_no'] = self.df['draw_no'].astype(int)

            # 최신 회차 번호 (내림차순 정렬되어 있다고 가정하지만, 혹시 몰라 최대값 추출)
            self.df = self.df.sort_values(by='draw_no', ascending=False).reset_index(drop=True)
            self.max_draw_no = self.df['draw_no'].max()

            # 모든 당첨 번호(보너스 포함) 리스트 생성 (빈도 분석용)
            self.all_numbers_flat = self.df[[f'num{i}' for i in range(1, 7)] + ['bonus_num']].values.flatten()
            self.all_numbers_flat = self.all_numbers_flat[~pd.isna(self.all_numbers_flat)].astype(int) # NaN 제거

            print(f"Lotto data loaded successfully. Total draws: {len(self.df)}")
            print(f"Latest draw number: {self.max_draw_no}")

        except FileNotFoundError:
            QMessageBox.critical(None, "파일 오류", f"'{self.csv_path}' 파일을 찾을 수 없습니다.\n"
                                                 "코드가 있는 폴더에 '로또.csv' 파일을 올바른 형식으로 넣어주세요.")
            sys.exit(1)
        except Exception as e:
            QMessageBox.critical(None, "데이터 로드 오류", f"로또 데이터를 로드하는 중 오류가 발생했습니다: {e}")
            sys.exit(1)

    # --- 데이터 조회 기능 ---
    def get_draw_by_no(self, draw_no):
        result = self.df[self.df['draw_no'] == draw_no]
        return result.to_dict('records')[0] if not result.empty else None

    def get_draws_by_date_range(self, start_date, end_date):
        # QDate 객체를 datetime 객체로 변환
        start_date_dt = pd.to_datetime(start_date.toString(Qt.DateFormat.ISODate))
        end_date_dt = pd.to_datetime(end_date.toString(Qt.DateFormat.ISODate))
        filtered_df = self.df[(self.df['draw_date'] >= start_date_dt) & (self.df['draw_date'] <= end_date_dt)]
        return filtered_df.to_dict('records')

    def get_draws_by_numbers(self, search_numbers, match_all=True, include_bonus=True):
        search_numbers_set = set(search_numbers) # 검색 효율을 위해 set 사용
        results = []
        for _, row in self.df.iterrows():
            draw_numbers = set(row[[f'num{i}' for i in range(1, 7)]].tolist())
            if include_bonus:
                draw_numbers.add(row['bonus_num'])

            if match_all: # 모든 번호 포함
                if search_numbers_set.issubset(draw_numbers):
                    results.append(row.to_dict())
            else: # 하나라도 포함
                if not search_numbers_set.isdisjoint(draw_numbers):
                    results.append(row.to_dict())
        return results

    # --- 데이터 분석 기능 ---
    def get_number_frequency(self, include_bonus=True):
        if include_bonus:
            numbers_to_count = self.all_numbers_flat
        else:
            numbers_to_count = self.df[[f'num{i}' for i in range(1, 7)]].values.flatten()
            numbers_to_count = numbers_to_count[~pd.isna(numbers_to_count)].astype(int)

        freq = pd.Series(numbers_to_count).value_counts().sort_index()
        total_counts = freq.sum()
        freq_df = pd.DataFrame({'number': freq.index, 'count': freq.values})
        freq_df['percentage'] = (freq_df['count'] / total_counts * 100).round(2)
        freq_df = freq_df.sort_values(by='count', ascending=False).reset_index(drop=True)
        return freq_df.to_dict('records')

    def get_gap_analysis(self):
        gap_data = {}
        for num in range(1, 46):
            # 메인 번호와 보너스 번호를 모두 포함하여 검색
            cols_to_search = [f'num{i}' for i in range(1, 7)] + ['bonus_num']
            
            # 해당 번호가 등장한 회차들을 찾고, 가장 최근 회차를 가져옴
            found_draws = self.df[self.df[cols_to_search].isin([num]).any(axis=1)]
            
            if not found_draws.empty:
                last_draw_no = found_draws['draw_no'].max()
                gap = self.max_draw_no - last_draw_no
                gap_data[num] = gap
            else: # 한 번도 나오지 않은 번호
                gap_data[num] = self.max_draw_no # 가장 최근 회차까지의 모든 회차에서 나오지 않음 (최대값)
        
        # 딕셔너리를 리스트 오브 딕셔너리로 변환하여 반환
        result_list = []
        for num, gap in gap_data.items():
            last_seen_draw_no = self.max_draw_no - gap
            if last_seen_draw_no <= 0: # 한 번도 나오지 않았거나 오류
                last_seen_draw_str = "N/A"
            else:
                last_seen_draw_str = str(last_seen_draw_no)
                
            result_list.append({'number': num, 'last_seen_draw': last_seen_draw_str, 'gap': gap})
        
        return sorted(result_list, key=lambda x: x['gap'], reverse=True) # 가장 오래 안 나온 번호부터 정렬

    def get_top_n_frequencies(self, n, include_bonus=True, ascending=False):
        freq_df = pd.DataFrame(self.get_number_frequency(include_bonus))
        if ascending: # 적게 나온 번호
            return freq_df.sort_values(by='count', ascending=True).head(n).to_dict('records')
        else: # 많이 나온 번호
            return freq_df.sort_values(by='count', ascending=False).head(n).to_dict('records')

    def get_pair_frequencies(self, pair_size=2, top_n=10):
        if pair_size not in [2, 3]:
            return []

        from itertools import combinations
        pair_counts = {}

        for _, row in self.df.iterrows():
            main_numbers = sorted(row[[f'num{i}' for i in range(1, 7)]].tolist())
            for combo in combinations(main_numbers, pair_size):
                key = tuple(sorted(combo)) # 튜플로 변환하여 정렬된 키 사용
                pair_counts[key] = pair_counts.get(key, 0) + 1

        sorted_pairs = sorted(pair_counts.items(), key=lambda item: item[1], reverse=True)
        
        results = []
        for pair, count in sorted_pairs[:top_n]:
            results.append({'pair': ', '.join(map(str, pair)), 'count': count})
        return results

    # --- 예측 기능 ---
    def generate_random_numbers(self, count=6, exclude_numbers=None, include_numbers=None):
        all_possible = list(range(1, 46))
        
        if exclude_numbers is None:
            exclude_numbers = []
        if include_numbers is None:
            include_numbers = []

        # 포함할 번호 먼저 추가
        predicted_set = set(include_numbers)
        
        # 제외 번호 제거
        all_possible = [num for num in all_possible if num not in exclude_numbers]
        
        # 이미 포함된 번호 제거
        all_possible = [num for num in all_possible if num not in predicted_set]

        # 필요한 만큼 나머지 번호 채우기
        remaining_to_pick = count - len(predicted_set)
        if remaining_to_pick < 0:
            QMessageBox.warning(None, "경고", f"포함할 번호({len(predicted_set)}개)가 6개를 초과합니다. 예측 시 앞쪽 6개만 사용됩니다.")
            return sorted(list(predicted_set)[:count])
        elif remaining_to_pick > len(all_possible):
            QMessageBox.warning(None, "경고", f"제외/포함 번호 설정으로 인해 유효한 번호 조합을 ({remaining_to_pick}개) 생성할 수 없습니다. 남은 번호 풀: {len(all_possible)}개")
            return [] # 또는 에러 처리
        
        predicted_set.update(random.sample(all_possible, remaining_to_pick))

        return sorted(list(predicted_set))

    def generate_statistical_numbers(self, count=6, exclude_numbers=None, include_numbers=None):
        
        freq_df = pd.DataFrame(self.get_number_frequency(include_bonus=True))
        
        if exclude_numbers is None:
            exclude_numbers = []
        if include_numbers is None:
            include_numbers = []

        predicted_set = set(include_numbers)
        
        # 제외 번호와 이미 포함된 번호를 제외한 후보군 생성
        candidate_numbers_with_freq = {
            row['number']: row['count'] for _, row in freq_df.iterrows()
            if row['number'] not in exclude_numbers and row['number'] not in predicted_set
        }

        # 후보군이 비어있으면 랜덤으로 대체
        if not candidate_numbers_with_freq:
            return self.generate_random_numbers(count, exclude_numbers, include_numbers)

        remaining_to_pick = count - len(predicted_set)
        if remaining_to_pick < 0:
            QMessageBox.warning(None, "경고", f"포함할 번호({len(predicted_set)}개)가 6개를 초과합니다. 예측 시 앞쪽 6개만 사용됩니다.")
            return sorted(list(predicted_set)[:count])
        elif remaining_to_pick > len(candidate_numbers_with_freq):
             QMessageBox.warning(None, "경고", f"제외/포함 번호 설정으로 인해 유효한 번호 조합을 ({remaining_to_pick}개) 생성할 수 없습니다. 남은 번호 풀: {len(candidate_numbers_with_freq)}개")
             return []

        # 가중치를 부여하기 위해 확률 분포를 생성 (빈도 비율 사용)
        candidates = list(candidate_numbers_with_freq.keys())
        weights = list(candidate_numbers_with_freq.values())
        
        if sum(weights) == 0: # 모든 후보 번호의 빈도가 0인 경우 (극히 드물겠지만)
             return self.generate_random_numbers(count, exclude_numbers, include_numbers)

        # random.choices를 사용하여 가중치 기반으로 추출
        picked = []
        while len(picked) < remaining_to_pick:
            new_pick = random.choices(candidates, weights=weights, k=1)[0]
            if new_pick not in predicted_set: # 중복 방지
                picked.append(new_pick)
                predicted_set.add(new_pick)
                
                # 한번 뽑힌 번호는 가중치 0으로 설정하여 다시 뽑히지 않도록
                try:
                    idx = candidates.index(new_pick)
                    weights[idx] = 0
                except ValueError:
                    pass # 이미 제외된 번호일 경우

        return sorted(list(predicted_set))
    
    # --- 내 번호 당첨 확인 ---
    def check_winnings(self, my_numbers):
        if len(my_numbers) != 6:
            return [] # 6개가 아닌 번호는 확인하지 않음

        my_numbers_set = set(my_numbers)
        winning_results = []

        for _, row in self.df.iterrows():
            draw_no = row['draw_no']
            draw_date = row['draw_date'].strftime('%Y-%m-%d')
            main_winning_nums = set(row[[f'num{i}' for i in range(1, 7)]].tolist())
            bonus_num = row['bonus_num']

            matched_main = len(my_numbers_set.intersection(main_winning_nums))
            matched_bonus = 1 if bonus_num in my_numbers_set else 0

            rank = "미당첨"
            if matched_main == 6:
                rank = "1등"
            elif matched_main == 5 and matched_bonus == 1:
                rank = "2등"
            elif matched_main == 5:
                rank = "3등"
            elif matched_main == 4:
                rank = "4등"
            elif matched_main == 3:
                rank = "5등"
            
            if rank != "미당첨":
                winning_results.append({
                    '회차': draw_no,
                    '날짜': draw_date,
                    '내 번호': ', '.join(map(str, my_numbers)),
                    '당첨 번호': ', '.join(map(str, sorted(list(main_winning_nums)))) + f' (보너스:{bonus_num})',
                    '일치 개수 (본)': matched_main,
                    '일치 개수 (보)': matched_bonus,
                    '등수': rank
                })
        return winning_results
