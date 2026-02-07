import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from collections import Counter
import warnings
from flask import Flask, render_template, request, redirect, url_for

# Suppress warnings for a clean output
warnings.filterwarnings("ignore")

app = Flask(__name__)

class LoanPredictionModel:
    def __init__(self, data_path):
        self.data = pd.read_csv(data_path)
        self._preprocess()
        self.best_model = None

    def _preprocess(self):
        self.data.columns = self.data.columns.str.strip()
        le = LabelEncoder()
        self.data['education'] = le.fit_transform(self.data['education'].str.strip())
        self.data['self_employed'] = le.fit_transform(self.data['self_employed'].str.strip())
        self.data['loan_status'] = self.data['loan_status'].apply(lambda x: 1 if x.strip() == 'Approved' else 0)
        self.X = self.data.drop(['loan_id', 'loan_status'], axis=1).values
        self.y = self.data['loan_status'].values

    def logistic_regression(self, X_train, y_train, X_test, iterations=1000, learning_rate=0.01):
        weights = np.zeros(X_train.shape[1])
        bias = 0
        for _ in range(iterations):
            linear_model = np.dot(X_train, weights) + bias
            predictions = 1 / (1 + np.exp(-linear_model))
            dw = (1 / len(y_train)) * np.dot(X_train.T, (predictions - y_train))
            db = (1 / len(y_train)) * np.sum(predictions - y_train)
            weights -= learning_rate * dw
            bias -= learning_rate * db
        predictions = 1 / (1 + np.exp(-np.dot(X_test, weights) + bias)) >= 0.5
        return predictions.astype(int), weights, bias

    class Node:
        def __init__(self, feature=None, threshold=None, left=None, right=None, value=None):
            self.feature = feature
            self.threshold = threshold
            self.left = left
            self.right = right
            self.value = value

    def build_tree(self, X, y):
        if len(set(y)) == 1:
            return self.Node(value=y[0])
        best_feature, best_threshold = self.best_split(X, y)
        left_indices = X[:, best_feature] < best_threshold
        right_indices = ~left_indices
        left = self.build_tree(X[left_indices], y[left_indices])
        right = self.build_tree(X[right_indices], y[right_indices])
        return self.Node(feature=best_feature, threshold=best_threshold, left=left, right=right)

    def best_split(self, X, y):
        best_gini = float('inf')
        best_feature, best_threshold = None, None
        for feature in range(X.shape[1]):
            thresholds = np.unique(X[:, feature])
            for threshold in thresholds:
                gini = self.gini_impurity(X[:, feature], y, threshold)
                if gini < best_gini:
                    best_gini, best_feature, best_threshold = gini, feature, threshold
        return best_feature, best_threshold

    def gini_impurity(self, feature_column, y, threshold):
        left_mask = feature_column < threshold
        right_mask = ~left_mask
        left_gini = 1.0 - sum((np.sum(left_mask & (y == c)) / np.sum(left_mask)) ** 2 for c in np.unique(y))
        right_gini = 1.0 - sum((np.sum(right_mask & (y == c)) / np.sum(right_mask)) ** 2 for c in np.unique(y))
        return (np.sum(left_mask) * left_gini + np.sum(right_mask) * right_gini) / len(y)

    def decision_tree_predict(self, node, X):
        if node.value is not None:
            return node.value
        if X[node.feature] < node.threshold:
            return self.decision_tree_predict(node.left, X)
        else:
            return self.decision_tree_predict(node.right, X)

    def random_forest(self, X_train, y_train, X_test, n_trees=3):
        trees = [self.build_tree(X_train, y_train) for _ in range(n_trees)]
        predictions = np.array([self.decision_tree_predict(tree, x) for tree in trees for x in X_test])
        predictions = predictions.reshape(n_trees, -1).T
        return np.array([Counter(row).most_common(1)[0][0] for row in predictions])

    def accuracy(self, y_pred, y_test):
        return np.sum(y_pred == y_test) / len(y_test)

    def train_models(self):
        X_train, X_test, y_train, y_test = train_test_split(self.X, self.y, test_size=0.3, stratify=self.y, random_state=42)
        log_preds, _, _ = self.logistic_regression(X_train, y_train, X_test)
        log_accuracy = self.accuracy(log_preds, y_test)

        tree = self.build_tree(X_train, y_train)
        tree_preds = np.array([self.decision_tree_predict(tree, x) for x in X_test])
        tree_accuracy = self.accuracy(tree_preds, y_test)

        rf_preds = self.random_forest(X_train, y_train, X_test)
        rf_accuracy = self.accuracy(rf_preds, y_test)

        accuracies = {"Logistic Regression": log_accuracy, "Decision Tree": tree_accuracy, "Random Forest": rf_accuracy}
        self.best_model = max(accuracies, key=accuracies.get)

        return accuracies

    def predict(self, user_input):
        if self.best_model == "Logistic Regression":
            pred, _, _ = self.logistic_regression([user_input], [], [])
            return "Approved" if pred[0] == 1 else "Not Approved", "Logistic Regression Prediction"
        elif self.best_model == "Decision Tree":
            tree = self.build_tree(self.X, self.y)
            pred = self.decision_tree_predict(tree, user_input)
            return "Approved" if pred == 1 else "Not Approved", "Decision Tree Prediction"
        else:
            rf_preds = self.random_forest(self.X, self.y, [user_input])
            return "Approved" if rf_preds[0] == 1 else "Not Approved", "Random Forest Prediction"

# Initialize and train the model once when the app starts
model = LoanPredictionModel(data_path='data.csv')
model_accuracy = model.train_models()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    user_data = request.form.to_dict()

    try:
        input_features = np.array([
            int(user_data['no_of_dependents']),
            1 if user_data['education'] == 'Graduate' else 0,
            1 if user_data['self_employed'] == 'Yes' else 0,
            float(user_data['income_annum']),
            float(user_data['loan_amount']),
            int(user_data['loan_term']),
            int(user_data['cibil_score']),
            float(user_data['residential_assets_value']),
            float(user_data['commercial_assets_value']),
            float(user_data['luxury_assets_value']),
            float(user_data['bank_asset_value'])
        ], dtype=float)
    except ValueError:
        return redirect(url_for('failure', calculations="Invalid input data."))

    # Get predictions based on the best model
    prediction, model_used = model.predict(input_features)

    if prediction == "Approved":
        return redirect(url_for('success', predictions=prediction, model=model))
    else:
        return redirect(url_for('failure', calculations="Loan not approved due to low income or Cibil_Score."))

@app.route('/success')
def success():
    predictions = request.args.get('predictions')
    model = request.args.get('model')
    return render_template('success.html', predictions=predictions, model=model)

@app.route('/failure')
def failure():
    calculations = request.args.get('calculations')
    return render_template('failure.html', calculations=calculations,model=model)

if __name__ == '__main__':
    app.run(debug=True, port= 5001)
