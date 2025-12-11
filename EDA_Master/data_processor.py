# data_processor.py
"""
데이터 처리 로직을 중앙화한 모듈
main.py에서 분리하여 재사용성과 테스트 용이성 향상
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler, RobustScaler, MaxAbsScaler

class DataProcessor:
    """데이터 전처리 작업을 담당하는 클래스"""
    
    @staticmethod
    def fill_missing_mean(df, columns):
        """결측치를 평균으로 채우기"""
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].mean(), inplace=True)
        return df
    
    @staticmethod
    def fill_missing_median(df, columns):
        """결측치를 중앙값으로 채우기"""
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col].fillna(df[col].median(), inplace=True)
        return df
    
    @staticmethod
    def fill_missing_mode(df, columns):
        """결측치를 최빈값으로 채우기"""
        for col in columns:
            if not df[col].empty:
                df[col].fillna(df[col].mode()[0], inplace=True)
        return df
    
    @staticmethod
    def drop_rows_with_nan(df, columns=None):
        """결측치 포함 행 제거"""
        if columns:
            df.dropna(subset=columns, inplace=True)
        else:
            df.dropna(inplace=True)
        return df
    
    @staticmethod
    def drop_columns_with_nan(df, columns=None):
        """결측치 포함 열 제거"""
        if columns:
            df.drop(columns=columns, inplace=True)
        else:
            df.dropna(axis=1, how='all', inplace=True)
        return df
    
    @staticmethod
    def remove_outliers_iqr(df, columns):
        """IQR 방식으로 이상치 제거"""
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                df = df[~((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR)))]
        return df
    
    @staticmethod
    def cap_outliers_iqr(df, columns):
        """IQR 방식으로 이상치 상/하한 적용"""
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                df[col] = df[col].clip(lower=Q1 - 1.5 * IQR, upper=Q3 + 1.5 * IQR)
        return df
    
    @staticmethod
    def label_encode(df, columns):
        """레이블 인코딩"""
        for col in columns:
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))
        return df
    
    @staticmethod
    def one_hot_encode(df, columns):
        """원-핫 인코딩"""
        df = pd.get_dummies(df, columns=columns, prefix=columns, dtype=int)
        return df
    
    @staticmethod
    def create_squared_features(df, columns):
        """제곱 특성 생성"""
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[f"{col}_squared"] = df[col] ** 2
        return df
    
    @staticmethod
    def extract_datetime_features(df, columns):
        """시계열 특성 추출"""
        for col in columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[f"{col}_year"] = df[col].dt.year
                df[f"{col}_month"] = df[col].dt.month
                df[f"{col}_day"] = df[col].dt.day
                df[f"{col}_dayofweek"] = df[col].dt.dayofweek
        return df
    
    @staticmethod
    def apply_scaling(df, columns, scaler_type='minmax'):
        """스케일링 적용"""
        scaler_map = {
            'minmax': MinMaxScaler(),
            'standard': StandardScaler(),
            'robust': RobustScaler(),
            'maxabs': MaxAbsScaler()
        }
        
        scaler = scaler_map.get(scaler_type.lower(), MinMaxScaler())
        num_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]
        
        if num_cols:
            df[num_cols] = scaler.fit_transform(df[num_cols].fillna(0))
        return df
    
    @staticmethod
    def convert_to_numeric(df, columns):
        """데이터 타입을 숫자로 변환"""
        for col in columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    
    @staticmethod
    def clean_text(df, columns):
        """텍스트 데이터 전처리 (공백 제거/소문자)"""
        for col in columns:
            df[col] = df[col].astype(str).str.strip().str.lower()
        return df
    
    @staticmethod
    def drop_duplicates(df, columns=None):
        """중복 데이터 제거"""
        if columns:
            df.drop_duplicates(subset=columns, inplace=True)
        else:
            df.drop_duplicates(inplace=True)
        return df
    
    @staticmethod
    def remove_low_variance(df, threshold=0.01):
        """낮은 분산 변수 제거"""
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            if df[col].var() < threshold:
                df.drop(columns=[col], inplace=True)
        return df
    
    @staticmethod
    def check_negative_values(df, columns):
        """음수값 체크"""
        results = {}
        for col in columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                count = (df[col] < 0).sum()
                results[col] = count
        return results
    
    @staticmethod
    def filter_data(df, column, operator, value):
        """
        데이터 필터링
        
        Parameters:
        -----------
        df : DataFrame
        column : str
            필터링할 컬럼
        operator : str
            '==', '!=', '>', '<', '>=', '<=', 'contains', 'startswith', 'endswith'
        value : any
            비교값
        """
        if operator == '==':
            return df[df[column] == value]
        elif operator == '!=':
            return df[df[column] != value]
        elif operator == '>':
            return df[df[column] > value]
        elif operator == '<':
            return df[df[column] < value]
        elif operator == '>=':
            return df[df[column] >= value]
        elif operator == '<=':
            return df[df[column] <= value]
        elif operator == 'contains':
            return df[df[column].astype(str).str.contains(str(value), na=False)]
        elif operator == 'startswith':
            return df[df[column].astype(str).str.startswith(str(value), na=False)]
        elif operator == 'endswith':
            return df[df[column].astype(str).str.endswith(str(value), na=False)]
        else:
            raise ValueError(f"지원하지 않는 연산자: {operator}")
