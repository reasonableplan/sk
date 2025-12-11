# ml_engine.py
import pandas as pd
import numpy as np
import pickle
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report, r2_score, mean_absolute_error

# LightGBM은 선택적 import (설치되어 있지 않을 수 있음)
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

def save_model(model, filepath):
    """모델을 파일로 저장"""
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)
    return filepath

def load_model(filepath):
    """파일에서 모델 로드"""
    with open(filepath, 'rb') as f:
        return pickle.load(f)

def run_ml_pipeline(X, y, is_cls, params, model_type='xgboost', use_cv=False, cv_folds=5, tune_hyperparams=False):
    """
    통합 ML 파이프라인
    
    Parameters:
    -----------
    X : DataFrame
        특성 데이터
    y : Series
        타겟 변수
    is_cls : bool
        분류 문제 여부
    params : dict
        모델 하이퍼파라미터
    model_type : str
        'xgboost', 'randomforest', 'lightgbm' 중 선택
    use_cv : bool
        교차 검증 사용 여부
    cv_folds : int
        교차 검증 폴드 수
    tune_hyperparams : bool
        하이퍼파라미터 튜닝 여부
    
    Returns:
    --------
    tuple : (model, results, feature_names)
    """
    numeric_features = X.select_dtypes(include=['number']).columns
    categorical_features = X.select_dtypes(include=['object', 'category']).columns

    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])

    le = None
    num_classes = None
    
    if is_cls:
        le = LabelEncoder()
        y = pd.Series(le.fit_transform(y.astype(str)))
        num_classes = y.nunique()
    
    # 모델 선택
    if model_type == 'xgboost':
        model = _get_xgboost_model(is_cls, num_classes, params)
    elif model_type == 'randomforest':
        model = _get_randomforest_model(is_cls, params)
    elif model_type == 'lightgbm':
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM이 설치되어 있지 않습니다. pip install lightgbm을 실행하세요.")
        model = _get_lightgbm_model(is_cls, num_classes, params)
    else:
        raise ValueError(f"지원하지 않는 모델 타입: {model_type}")

    clf = Pipeline(steps=[('preprocessor', preprocessor), ('classifier', model)])

    # 데이터 분할
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, 
        stratify=y if is_cls else None
    )
    
    # 하이퍼파라미터 튜닝
    if tune_hyperparams:
        clf = _tune_hyperparameters(clf, X_train, y_train, is_cls, model_type)
    
    # 모델 학습
    clf.fit(X_train, y_train)
    
    # 결과 계산
    res = _calculate_results(clf, X_train, X_test, y_train, y_test, is_cls, le, num_classes, use_cv, cv_folds)
    res['model_type'] = model_type
    
    # 특성 이름 추출
    feature_names = _extract_feature_names(clf, numeric_features, categorical_features)
    
    model_obj = clf.named_steps['classifier']
    
    return model_obj, res, feature_names

def _get_xgboost_model(is_cls, num_classes, params):
    """XGBoost 모델 생성"""
    if is_cls:
        if num_classes and num_classes > 2:
            params['objective'] = 'multi:softmax'
            params['num_class'] = num_classes
            eval_metric = 'mlogloss'
        else:
            params['objective'] = 'binary:logistic'
            eval_metric = 'logloss'
        return xgb.XGBClassifier(eval_metric=eval_metric, use_label_encoder=False, **params)
    else:
        return xgb.XGBRegressor(**params)

def _get_randomforest_model(is_cls, params):
    """RandomForest 모델 생성"""
    # XGBoost 파라미터를 RandomForest 파라미터로 변환
    rf_params = {
        'n_estimators': params.get('n_estimators', 100),
        'max_depth': params.get('max_depth', None),
        'random_state': 42,
        'n_jobs': -1
    }
    
    if is_cls:
        return RandomForestClassifier(**rf_params)
    else:
        return RandomForestRegressor(**rf_params)

def _get_lightgbm_model(is_cls, num_classes, params):
    """LightGBM 모델 생성"""
    lgb_params = {
        'n_estimators': params.get('n_estimators', 100),
        'max_depth': params.get('max_depth', -1),
        'learning_rate': params.get('learning_rate', 0.1),
        'random_state': 42,
        'verbose': -1
    }
    
    if is_cls:
        if num_classes and num_classes > 2:
            lgb_params['objective'] = 'multiclass'
            lgb_params['num_class'] = num_classes
        else:
            lgb_params['objective'] = 'binary'
        return lgb.LGBMClassifier(**lgb_params)
    else:
        return lgb.LGBMRegressor(**lgb_params)

def _tune_hyperparameters(clf, X_train, y_train, is_cls, model_type):
    """간단한 하이퍼파라미터 튜닝"""
    if model_type == 'xgboost':
        param_grid = {
            'classifier__n_estimators': [100, 200],
            'classifier__max_depth': [3, 5, 7],
            'classifier__learning_rate': [0.01, 0.1]
        }
    elif model_type == 'randomforest':
        param_grid = {
            'classifier__n_estimators': [100, 200],
            'classifier__max_depth': [None, 10, 20]
        }
    else:  # lightgbm
        param_grid = {
            'classifier__n_estimators': [100, 200],
            'classifier__max_depth': [3, 5, 7]
        }
    
    scoring = 'accuracy' if is_cls else 'r2'
    grid_search = GridSearchCV(clf, param_grid, cv=3, scoring=scoring, n_jobs=-1, verbose=0)
    grid_search.fit(X_train, y_train)
    
    return grid_search.best_estimator_

def _calculate_results(clf, X_train, X_test, y_train, y_test, is_cls, le, num_classes, use_cv, cv_folds):
    """결과 계산"""
    res = {}
    
    if is_cls:
        preds = clf.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        report = classification_report(y_test, preds, output_dict=True)
        res = {'type': 'Classification', 'accuracy': accuracy, 'report': report}
        
        if le:
            res['original_labels'] = le.inverse_transform(range(num_classes))
        
        # 교차 검증
        if use_cv:
            cv_scores = cross_val_score(clf, X_train, y_train, cv=cv_folds, scoring='accuracy')
            res['cv_mean'] = cv_scores.mean()
            res['cv_std'] = cv_scores.std()
    else:
        preds = clf.predict(X_test)
        mse = mean_squared_error(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        r2 = r2_score(y_test, preds)
        res = {'type': 'Regression', 'mse': mse, 'mae': mae, 'r2': r2}
        
        # 교차 검증
        if use_cv:
            cv_scores = cross_val_score(clf, X_train, y_train, cv=cv_folds, scoring='r2')
            res['cv_mean'] = cv_scores.mean()
            res['cv_std'] = cv_scores.std()
    
    return res

def _extract_feature_names(clf, numeric_features, categorical_features):
    """특성 이름 추출"""
    try:
        try:
            cat_cols = clf.named_steps['preprocessor'].named_transformers_['cat'].named_steps['onehot'].get_feature_names_out(categorical_features)
        except:
            cat_cols = []
        return list(numeric_features) + list(cat_cols)
    except Exception:
        return [f"Feature_{i}" for i in range(len(numeric_features) + len(categorical_features))]

# 하위 호환성을 위한 별칭
run_xgboost_pipeline = lambda X, y, is_cls, params: run_ml_pipeline(X, y, is_cls, params, model_type='xgboost')
