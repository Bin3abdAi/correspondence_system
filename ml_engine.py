import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

class DeepLearningAnalyticsEngine:
    def __init__(self):
        self.mlp_model = MLPClassifier(hidden_layer_sizes=(64, 32, 16), max_iter=300, random_state=42)
        self.kmeans_model = KMeans(n_clusters=4, random_state=42)
        self.encoders = {}
        self.scaler = StandardScaler()
        self.is_trained = False
        self.accuracy = 0.0

    def train_models(self, df: pd.DataFrame):
        """تدريب نموذج الشبكة العصبية الاصطناعية على 2500 معاملة"""
        if df.empty or len(df) < 100:
            return False, 0.0

        data = df.copy()
        
        # تجهيز الهدف (Target): هل المعاملة متأخرة/غير منجزة؟ (1 = غير منجزة/متأخرة, 0 = منجزة)
        data['target'] = (data['الحالة'] != 'منجزة').astype(int)

        categorical_cols = ['الحي', 'نوع الجهة', 'درجة الأهمية', 'السرية', 'القسم المكلف']
        for col in categorical_cols:
            le = LabelEncoder()
            data[col + '_enc'] = le.fit_transform(data[col].astype(str))
            self.encoders[col] = le

        feature_cols = [col + '_enc' for col in categorical_cols]
        X = data[feature_cols]
        y = data['target']

        X_scaled = self.scaler.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
        
        # تدريب الشبكة العصبية
        self.mlp_model.fit(X_train, y_train)
        y_pred = self.mlp_model.predict(X_test)
        self.accuracy = round(accuracy_score(y_test, y_pred) * 100, 2)
        
        # تدريب K-Means لتقسيم المعاملات إلى تكتلات جغرافية وإدارية Hotspots
        self.kmeans_model.fit(X_scaled)
        
        self.is_trained = True
        return True, self.accuracy

    def predict_delay_risk(self, district, sender_type, priority, confidentiality, dept):
        """التنبؤ بنسبة وتأخير معاملة جديدة عبر الشبكة العصبية"""
        if not self.is_trained:
            return 0.5, "النموذج قيد التهيئة"

        try:
            row = []
            inputs = {
                'الحي': district,
                'نوع الجهة': sender_type,
                'درجة الأهمية': priority,
                'السرية': confidentiality,
                'القسم المكلف': dept
            }
            for col, val in inputs.items():
                le = self.encoders[col]
                # معالجة القيم الجديدة غير المسجلة
                if val in le.classes_:
                    enc_val = le.transform([val])[0]
                else:
                    enc_val = 0
                row.append(enc_val)

            row_scaled = self.scaler.transform([row])
            prob = self.mlp_model.predict_proba(row_scaled)[0][1] # احتمال التأخير
            
            risk_label = "حرج جداً (تأخير مؤكد)" if prob > 0.75 else ("عالي" if prob > 0.5 else "منخفض")
            return round(prob * 100, 1), risk_label
        except Exception as e:
            return 50.0, f"خطأ تنبؤ: {str(e)}"
        