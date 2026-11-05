"""ML / DL / RL bilingual learning calculator (Tkinter + NumPy).

실행:
    pip install numpy
    python ml_dl_rl_calculator_bilingual.py
English UI:
    python ml_dl_rl_calculator_bilingual.py --lang en
테스트:
    python ml_dl_rl_calculator_bilingual.py --test

교육용 계산기입니다. 입력값은 쉼표/공백으로 구분하고,
행렬은 세미콜론(;) 또는 줄바꿈으로 행을 구분합니다.
"""

from __future__ import annotations

import math
import re
import sys
import unittest
from dataclasses import dataclass
from typing import Callable

import numpy as np


# ------------------------- 입력 및 계산 헬퍼 -------------------------

def number(value: str, *, name: str = '값') -> float:
    try:
        out = float(value.strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f'{name}: 유효한 숫자를 입력하세요.') from exc
    if not math.isfinite(out):
        raise ValueError(f'{name}: NaN/무한대는 사용할 수 없습니다.')
    return out


def integer(value: str, *, name: str = '값', minimum: int | None = None) -> int:
    raw = number(value, name=name)
    if not raw.is_integer():
        raise ValueError(f'{name}: 정수를 입력하세요.')
    out = int(raw)
    if minimum is not None and out < minimum:
        raise ValueError(f'{name}: {minimum} 이상의 정수를 입력하세요.')
    return out


def vector(value: str, *, name: str = '벡터') -> np.ndarray:
    s = value.strip()
    if s.startswith('[') and s.endswith(']'):
        s = s[1:-1].strip()
    parts = [x for x in re.split(r'[,\s]+', s) if x]
    if not parts:
        raise ValueError(f'{name}: 숫자를 하나 이상 입력하세요.')
    return np.asarray([number(x, name=name) for x in parts], dtype=float)


def matrix(value: str, *, name: str = '행렬') -> np.ndarray:
    rows = [r.strip() for r in re.split(r'[;\n]+', value.strip()) if r.strip()]
    if not rows:
        raise ValueError(f'{name}: 행을 입력하세요.')
    arrays = [vector(row, name=f'{name} {i+1}행') for i, row in enumerate(rows)]
    if len(set(len(a) for a in arrays)) != 1:
        raise ValueError(f'{name}: 모든 행의 열 개수가 같아야 합니다.')
    return np.vstack(arrays)


def same_size(a: np.ndarray, b: np.ndarray) -> None:
    if a.shape != b.shape:
        raise ValueError(f'데이터 크기가 일치하지 않습니다: {a.shape} / {b.shape}')


def between(x: float, low: float, high: float, name: str) -> float:
    if not low <= x <= high:
        raise ValueError(f'{name}: {low}~{high} 범위로 입력하세요.')
    return x


def format_result(obj: object) -> str:
    if isinstance(obj, np.ndarray):
        return np.array2string(obj, precision=6, suppress_small=True)
    if isinstance(obj, dict):
        return '\n'.join(f'{k}: {format_result(v)}' for k, v in obj.items())
    if isinstance(obj, (float, np.floating)):
        return f'{float(obj):.8g}'
    return str(obj)


# ------------------------------ ML ---------------------------------

def ml_linear(v: dict[str, str]) -> object:
    x, w = vector(v['x'], name='x'), vector(v['w'], name='w')
    same_size(x, w)
    return float(np.dot(x, w) + number(v['b'], name='b'))


def ml_mse(v: dict[str, str]) -> object:
    y, p = vector(v['y'], name='정답'), vector(v['p'], name='예측')
    same_size(y, p)
    return float(np.mean((y - p) ** 2))


def ml_mae(v: dict[str, str]) -> object:
    y, p = vector(v['y'], name='정답'), vector(v['p'], name='예측')
    same_size(y, p)
    return float(np.mean(np.abs(y - p)))


def ml_accuracy(v: dict[str, str]) -> object:
    y, p = vector(v['y'], name='정답'), vector(v['p'], name='예측')
    same_size(y, p)
    return float(np.mean(y == p))


def ml_binary_metrics(v: dict[str, str]) -> object:
    y, p = vector(v['y'], name='정답'), vector(v['p'], name='예측')
    same_size(y, p)
    if not (np.isin(y, [0, 1]).all() and np.isin(p, [0, 1]).all()):
        raise ValueError('Precision/Recall/F1은 이진 레이블 0 또는 1만 허용합니다.')
    tp = int(np.sum((y == 1) & (p == 1)))
    tn = int(np.sum((y == 0) & (p == 0)))
    fp = int(np.sum((y == 0) & (p == 1)))
    fn = int(np.sum((y == 1) & (p == 0)))
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {'TP': tp, 'TN': tn, 'FP': fp, 'FN': fn,
            'Precision': precision, 'Recall': recall, 'F1': f1}


def ml_bce(v: dict[str, str]) -> object:
    y, p = vector(v['y'], name='정답'), vector(v['p'], name='예측 확률')
    same_size(y, p)
    if not np.isin(y, [0, 1]).all():
        raise ValueError('정답은 이진 레이블 0 또는 1이어야 합니다.')
    if not ((0 <= p).all() and (p <= 1).all()):
        raise ValueError('예측 확률은 0~1 사이여야 합니다.')
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


# ------------------------------ DL ---------------------------------

def dl_sigmoid(v: dict[str, str]) -> object:
    x = vector(v['x'], name='입력 x')
    # 음수와 양수를 분리해 overflow 없이 계산
    positive = x >= 0
    result = np.empty_like(x)
    result[positive] = 1 / (1 + np.exp(-x[positive]))
    exp_x = np.exp(x[~positive])
    result[~positive] = exp_x / (1 + exp_x)
    return result


def dl_relu(v: dict[str, str]) -> object:
    return np.maximum(0.0, vector(v['x'], name='입력 x'))


def dl_softmax(v: dict[str, str]) -> object:
    x = vector(v['x'], name='로짓 x')
    ex = np.exp(x - np.max(x))
    return ex / np.sum(ex)


def dl_dense(v: dict[str, str]) -> object:
    x, w, b = vector(v['x'], name='x'), matrix(v['w'], name='W'), vector(v['b'], name='b')
    if w.shape[1] != len(x) or w.shape[0] != len(b):
        raise ValueError(f'크기 오류: W={w.shape}, x={x.shape}, b={b.shape}. W열=x길이, W행=b길이여야 합니다.')
    return w @ x + b


def dl_params(v: dict[str, str]) -> object:
    ni = integer(v['ni'], name='입력 뉴런', minimum=1)
    no = integer(v['no'], name='출력 뉴런', minimum=1)
    use_bias = integer(v['bias'], name='바이어스 사용(0/1)', minimum=0)
    if use_bias not in (0, 1):
        raise ValueError('바이어스 사용은 0 또는 1이어야 합니다.')
    return {'Weights': ni * no, 'Biases': no if use_bias else 0,
            'Total parameters': ni * no + (no if use_bias else 0)}


def dl_conv_output(v: dict[str, str]) -> object:
    h = integer(v['h'], name='입력 크기', minimum=1)
    k = integer(v['k'], name='커널 크기', minimum=1)
    p = integer(v['p'], name='패딩', minimum=0)
    s = integer(v['s'], name='스트라이드', minimum=1)
    d = integer(v['d'], name='딜레이션', minimum=1)
    numerator = h + 2 * p - d * (k - 1) - 1
    if numerator < 0:
        raise ValueError('커널이 입력/패딩보다 큽니다. 출력 크기가 정의되지 않습니다.')
    return {'Output size (1D)': numerator // s + 1}


def dl_gradient(v: dict[str, str]) -> object:
    w, g = vector(v['w'], name='현재 가중치'), vector(v['g'], name='기울기')
    same_size(w, g)
    lr = number(v['lr'], name='학습률')
    if lr <= 0:
        raise ValueError('학습률은 0보다 커야 합니다.')
    return w - lr * g


# ------------------------------ RL ---------------------------------

def rl_return(v: dict[str, str]) -> object:
    r = vector(v['r'], name='보상들')
    gamma = between(number(v['gamma'], name='감가율 γ'), 0, 1, 'γ')
    return float(sum(float(reward) * gamma ** i for i, reward in enumerate(r)))


def rl_td_target(v: dict[str, str]) -> object:
    r = number(v['r'], name='보상')
    gamma = between(number(v['gamma'], name='γ'), 0, 1, 'γ')
    vnext = number(v['vnext'], name='다음 상태 가치')
    done = integer(v['done'], name='종료(0/1)', minimum=0)
    if done not in (0, 1):
        raise ValueError('종료 여부는 0 또는 1이어야 합니다.')
    return r + (0 if done else gamma * vnext)


def rl_td_error(v: dict[str, str]) -> object:
    target = rl_td_target(v)
    current = number(v['current'], name='현재 상태 가치')
    return {'TD target': target, 'TD error': target - current}


def rl_q_update(v: dict[str, str]) -> object:
    q = number(v['q'], name='기존 Q')
    alpha = between(number(v['alpha'], name='학습률 α'), 0, 1, 'α')
    gamma = between(number(v['gamma'], name='감가율 γ'), 0, 1, 'γ')
    r = number(v['r'], name='보상')
    next_q = vector(v['nextq'], name='다음 상태 Q 값들')
    done = integer(v['done'], name='종료(0/1)', minimum=0)
    if done not in (0, 1):
        raise ValueError('종료 여부는 0 또는 1이어야 합니다.')
    target = r + (0 if done else gamma * float(np.max(next_q)))
    updated = q + alpha * (target - q)
    return {'TD target': target, 'TD error': target - q, 'Updated Q': updated}


def rl_bellman_expect(v: dict[str, str]) -> object:
    probs = vector(v['probs'], name='전이 확률들')
    rewards = vector(v['rewards'], name='보상들')
    values = vector(v['values'], name='다음 상태 가치들')
    same_size(probs, rewards)
    same_size(probs, values)
    gamma = between(number(v['gamma'], name='γ'), 0, 1, 'γ')
    if (probs < 0).any() or (probs > 1).any() or not np.isclose(np.sum(probs), 1.0, rtol=0, atol=1e-8):
        raise ValueError('전이 확률은 모두 0~1이고, 합계는 1이어야 합니다.')
    return float(np.dot(probs, rewards + gamma * values))


def rl_epsilon_greedy(v: dict[str, str]) -> object:
    q = vector(v['q'], name='행동별 Q 값')
    eps = between(number(v['eps'], name='ε'), 0, 1, 'ε')
    winners = np.flatnonzero(q == np.max(q))
    probs = np.full(q.shape, eps / len(q))
    probs[winners] += (1 - eps) / len(winners)
    return {'Greedy action indexes (0-based)': winners,
            'Action selection probabilities': probs,
            'Probability sum': float(np.sum(probs))}


# --------------------------- 계산 메뉴 ------------------------------
@dataclass(frozen=True)
class Field:
    key: str
    label: str
    example: str


@dataclass(frozen=True)
class Operation:
    title: str
    description: str
    formula: str
    fields: tuple[Field, ...]
    compute: Callable[[dict[str, str]], object]


def f(key: str, label: str, example: str) -> Field:
    return Field(key, label, example)


MENU: dict[str, tuple[Operation, ...]] = {
    'ML': (
        Operation('선형 예측', '특성 벡터와 가중치를 이용한 선형 모델 예측', 'ŷ = w·x + b',
                  (f('x', '특성 x (벡터)', '1, 2, 3'), f('w', '가중치 w (벡터)', '0.2, 0.4, 0.6'), f('b', '편향 b', '0.1')), ml_linear),
        Operation('MSE', '회귀 평균제곱오차', 'MSE = mean((y − ŷ)²)',
                  (f('y', '정답 y', '1, 0, 1'), f('p', '예측 ŷ', '0.8, 0.1, 0.6')), ml_mse),
        Operation('MAE', '회귀 평균절대오차', 'MAE = mean(|y − ŷ|)',
                  (f('y', '정답 y', '1, 0, 1'), f('p', '예측 ŷ', '0.8, 0.1, 0.6')), ml_mae),
        Operation('Accuracy', '분류 정확도', 'Accuracy = 맞힌 수 / 전체 수',
                  (f('y', '정답 레이블', '1, 0, 1, 0'), f('p', '예측 레이블', '1, 0, 0, 0')), ml_accuracy),
        Operation('Precision / Recall / F1', '이진 분류 성능 평가(0/1)', 'P = TP/(TP+FP), R = TP/(TP+FN), F1 = 2PR/(P+R)',
                  (f('y', '정답(0/1)', '1, 0, 1, 0, 1'), f('p', '예측(0/1)', '1, 1, 1, 0, 0')), ml_binary_metrics),
        Operation('Binary Cross-Entropy', '이진 분류의 평균 교차엔트로피(자연로그)', 'BCE = −mean(y·ln(p) + (1−y)·ln(1−p))',
                  (f('y', '정답(0/1)', '1, 0, 1'), f('p', '양성(1) 예측확률', '0.9, 0.3, 0.7')), ml_bce),
    ),
    'DL': (
        Operation('Sigmoid', '시그모이드 활성화 함수', 'σ(x) = 1/(1+e^(−x))',
                  (f('x', '입력 벡터 x', '-2, 0, 2'),), dl_sigmoid),
        Operation('ReLU', 'ReLU 활성화 함수', 'ReLU(x) = max(0, x)',
                  (f('x', '입력 벡터 x', '-3, -1, 0, 2, 4'),), dl_relu),
        Operation('Softmax', '로짓을 확률분포로 변환(수치적으로 안정한 계산)', 'softmax(xᵢ) = exp(xᵢ−max(x)) / Σ exp(xⱼ−max(x))',
                  (f('x', '로짓 x', '1, 2, 3'),), dl_softmax),
        Operation('Dense Layer Forward', '완전연결층 한 층의 순전파', 'y = W·x + b (W: 출력×입력)',
                  (f('x', '입력 벡터 x', '1, 2'), f('w', '가중치 행렬 W (행은 ; 구분)', '0.2, 0.4; 0.6, 0.8'), f('b', '바이어스 벡터 b', '0.1, -0.1')), dl_dense),
        Operation('Dense Parameters', '완전연결층 파라미터 수', 'Weights = in×out; Bias = out (사용 시)',
                  (f('ni', '입력 뉴런 수', '128'), f('no', '출력 뉴런 수', '64'), f('bias', '바이어스 사용(1=예, 0=아니오)', '1')), dl_params),
        Operation('Convolution Output Size', '1차원 기준 합성곱 출력 길이(높이/너비 각각 적용 가능)', 'out = floor((in+2P−D(K−1)−1)/S+1)',
                  (f('h', '입력 길이', '32'), f('k', '커널 K', '3'), f('p', '패딩 P', '1'), f('s', '스트라이드 S', '2'), f('d', '딜레이션 D', '1')), dl_conv_output),
        Operation('Gradient Descent Step', '기울기 하강법 1회 업데이트', 'w_new = w − learning_rate×gradient',
                  (f('w', '현재 가중치 w', '1, 2, 3'), f('g', '기울기 gradient', '0.1, -0.2, 0.3'), f('lr', '학습률', '0.01')), dl_gradient),
    ),
    'RL': (
        Operation('Discounted Return', '주어진 보상열의 할인 누적 보상', 'G₀ = r₀ + γr₁ + γ²r₂ + …',
                  (f('r', '보상열 r', '1, 2, 3'), f('gamma', '할인율 γ (0~1)', '0.9')), rl_return),
        Operation('TD Target', '종료 상태 처리 포함 1-step TD 목표값', 'target = r + γ·V(next) (done=1이면 r)',
                  (f('r', '보상 r', '1'), f('gamma', '할인율 γ', '0.9'), f('vnext', '다음 상태 가치 V(next)', '5'), f('done', '에피소드 종료(0/1)', '0')), rl_td_target),
        Operation('TD Error', '1-step TD 오차', 'δ = [r+γV(next)] − V(current) (done 반영)',
                  (f('r', '보상 r', '1'), f('gamma', '할인율 γ', '0.9'), f('vnext', '다음 상태 가치', '5'), f('current', '현재 상태 가치', '4'), f('done', '에피소드 종료(0/1)', '0')), rl_td_error),
        Operation('Q-Learning Update', 'Q-learning 1회 오프폴리시 업데이트', 'Q_new = Q_old + α[r + γ·max Q(next,a) − Q_old] (done 반영)',
                  (f('q', '현재 Q(s,a)', '2'), f('alpha', '학습률 α (0~1)', '0.1'), f('r', '보상 r', '1'), f('gamma', '할인율 γ (0~1)', '0.9'), f('nextq', '다음 상태 행동별 Q값', '2, 4, 3'), f('done', '에피소드 종료(0/1)', '0')), rl_q_update),
        Operation('Bellman Expectation', '전이 확률 분포가 주어졌을 때 기대 목표값', 'E[r+γV(next)] = Σ pᵢ(rᵢ+γVᵢ)',
                  (f('probs', '전이 확률 p', '0.7, 0.3'), f('rewards', '결과별 보상 r', '1, -1'), f('values', '다음 상태 가치 V', '4, 2'), f('gamma', '할인율 γ', '0.9')), rl_bellman_expect),
        Operation('Epsilon-Greedy', 'ε-greedy의 행동별 선택 확률(최댓값 동률은 균등 분배)', 'P(a) = ε/|A| + (1−ε)/|argmax Q| (최적 행동일 때)',
                  (f('q', '행동별 Q 값', '2, 5, 5, 1'), f('eps', '탐험률 ε (0~1)', '0.1')), rl_epsilon_greedy),
    ),
}


# ------------------------ Korean / English UI ------------------------
# Computation functions and the original Korean MENU are retained unmodified.
# English translations are keyed by stable function names, not visible text.

UI = {
    'ko': {
        'window': 'ML · DL · RL 학습용 계산기',
        'language': '언어 / Language', 'select': '계산 항목 선택',
        'formula': '수식', 'calculate': '계산하기', 'reset': '예제값 복원',
        'copy': '결과 복사', 'result': '계산 결과',
        'hint': '벡터: 1, 2, 3  |  행렬: 1, 2; 3, 4',
        'ready': '예제값이 입력되었습니다. [계산하기]를 누르세요.',
        'calculated': '계산 완료', 'input_error': '입력 오류',
        'check': '입력값 확인 필요', 'first': '먼저 계산하세요.',
        'copied': '계산 결과를 클립보드에 복사했습니다.',
        'tab_ml': 'ML · 머신러닝', 'tab_dl': 'DL · 딥러닝',
        'tab_rl': 'RL · 강화학습',
    },
    'en': {
        'window': 'ML · DL · RL Learning Calculator',
        'language': 'Language / 언어', 'select': 'Select an operation',
        'formula': 'Formula', 'calculate': 'Calculate', 'reset': 'Restore examples',
        'copy': 'Copy result', 'result': 'Calculation result',
        'hint': 'Vector: 1, 2, 3  |  Matrix: 1, 2; 3, 4',
        'ready': 'Example values loaded. Click [Calculate].',
        'calculated': 'Calculation complete', 'input_error': 'Input error',
        'check': 'Please check the input values', 'first': 'Calculate something first.',
        'copied': 'Result copied to the clipboard.',
        'tab_ml': 'ML · Machine Learning', 'tab_dl': 'DL · Deep Learning',
        'tab_rl': 'RL · Reinforcement Learning',
    },
}

# title, description, formula, and per-input translations for each operation
EN_OPERATIONS = {
    'ml_linear': ('Linear Prediction', 'Predict with a feature vector, weights, and bias.',
                  'ŷ = w·x + b', {'x': 'Features x (vector)', 'w': 'Weights w (vector)', 'b': 'Bias b'}),
    'ml_mse': ('MSE', 'Mean squared error for regression.',
               'MSE = mean((y − ŷ)²)', {'y': 'True targets y', 'p': 'Predictions ŷ'}),
    'ml_mae': ('MAE', 'Mean absolute error for regression.',
               'MAE = mean(|y − ŷ|)', {'y': 'True targets y', 'p': 'Predictions ŷ'}),
    'ml_accuracy': ('Accuracy', 'Classification accuracy.',
                    'Accuracy = correct predictions / total samples',
                    {'y': 'True labels', 'p': 'Predicted labels'}),
    'ml_binary_metrics': ('Precision / Recall / F1', 'Evaluate binary classification (0/1).',
                          'P = TP/(TP+FP), R = TP/(TP+FN), F1 = 2PR/(P+R)',
                          {'y': 'True labels (0/1)', 'p': 'Predicted labels (0/1)'}),
    'ml_bce': ('Binary Cross-Entropy', 'Mean binary cross-entropy with natural logarithms.',
               'BCE = −mean(y·ln(p) + (1−y)·ln(1−p))',
               {'y': 'True labels (0/1)', 'p': 'Predicted P(class=1)'}),
    'dl_sigmoid': ('Sigmoid', 'Sigmoid activation function.',
                   'σ(x) = 1/(1+e^(−x))', {'x': 'Input vector x'}),
    'dl_relu': ('ReLU', 'Rectified linear unit activation.',
                'ReLU(x) = max(0, x)', {'x': 'Input vector x'}),
    'dl_softmax': ('Softmax', 'Convert logits to probabilities using stable arithmetic.',
                   'softmax(xᵢ) = exp(xᵢ−max(x)) / Σ exp(xⱼ−max(x))', {'x': 'Logits x'}),
    'dl_dense': ('Dense Layer Forward', 'Forward pass through a fully connected layer.',
                 'y = W·x + b (W: outputs × inputs)',
                 {'x': 'Input vector x', 'w': 'Weight matrix W (separate rows with ;)',
                  'b': 'Bias vector b'}),
    'dl_params': ('Dense Parameters', 'Count trainable parameters in a dense layer.',
                  'Weights = in×out; Biases = out (if enabled)',
                  {'ni': 'Number of input neurons', 'no': 'Number of output neurons',
                   'bias': 'Use bias? (1=yes, 0=no)'}),
    'dl_conv_output': ('Convolution Output Size',
                       '1D convolution output length (apply separately to height and width).',
                       'out = floor((in+2P−D(K−1)−1)/S+1)',
                       {'h': 'Input length', 'k': 'Kernel size K', 'p': 'Padding P',
                        's': 'Stride S', 'd': 'Dilation D'}),
    'dl_gradient': ('Gradient Descent Step', 'Perform one gradient descent update.',
                    'w_new = w − learning_rate×gradient',
                    {'w': 'Current weights w', 'g': 'Gradients g', 'lr': 'Learning rate'}),
    'rl_return': ('Discounted Return', 'Discounted sum of a reward sequence.',
                  'G₀ = r₀ + γr₁ + γ²r₂ + …', {'r': 'Rewards r', 'gamma': 'Discount factor γ (0–1)'}),
    'rl_td_target': ('TD Target', 'One-step TD target with terminal-state handling.',
                     'target = r + γ·V(next) (if done=1, target=r)',
                     {'r': 'Reward r', 'gamma': 'Discount factor γ',
                      'vnext': 'Next-state value V(next)', 'done': 'Terminal state? (0/1)'}),
    'rl_td_error': ('TD Error', 'One-step temporal-difference error.',
                    'δ = [r+γV(next)] − V(current) (terminal handling)',
                    {'r': 'Reward r', 'gamma': 'Discount factor γ',
                     'vnext': 'Next-state value', 'current': 'Current-state value',
                     'done': 'Terminal state? (0/1)'}),
    'rl_q_update': ('Q-Learning Update', 'One off-policy Q-learning update.',
                    'Q_new = Q_old + α[r + γ·max Q(next,a) − Q_old] (terminal handling)',
                    {'q': 'Current Q(s,a)', 'alpha': 'Learning rate α (0–1)',
                     'r': 'Reward r', 'gamma': 'Discount factor γ (0–1)',
                     'nextq': 'Next-state action Q values', 'done': 'Terminal state? (0/1)'}),
    'rl_bellman_expect': ('Bellman Expectation', 'Expected target with transition probabilities.',
                          'E[r+γV(next)] = Σ pᵢ(rᵢ+γVᵢ)',
                          {'probs': 'Transition probabilities p', 'rewards': 'Rewards by outcome r',
                           'values': 'Next-state values V', 'gamma': 'Discount factor γ'}),
    'rl_epsilon_greedy': ('Epsilon-Greedy',
                          'Action probabilities under ε-greedy; ties share probability equally.',
                          'P(a) = ε/|A| + (1−ε)/|argmax Q| (for optimal actions)',
                          {'q': 'Q value for each action', 'eps': 'Exploration rate ε (0–1)'}),
}

RESULT_KEYS_KO = {
    'TP': 'TP (진양성)', 'TN': 'TN (진음성)',
    'FP': 'FP (위양성)', 'FN': 'FN (위음성)',
    'Precision': '정밀도 (Precision)', 'Recall': '재현율 (Recall)', 'F1': 'F1 점수',
    'Weights': '가중치 수', 'Biases': '편향 수', 'Total parameters': '총 파라미터 수',
    'Output size (1D)': '출력 크기 (1D)',
    'TD target': 'TD 목표값', 'TD error': 'TD 오차', 'Updated Q': '갱신된 Q',
    'Greedy action indexes (0-based)': '최적 행동 인덱스 (0부터 시작)',
    'Action selection probabilities': '행동 선택 확률',
    'Probability sum': '확률 합계',
}

# Replace Korean parts of the original numeric-validation errors if English UI is selected.
# Longer substitutions go first so overlapping substrings do not cause partial replacements.
ERROR_EN = {
    'Precision/Recall/F1은 이진 레이블 0 또는 1만 허용합니다.':
        'Precision/Recall/F1 requires binary labels (0 or 1).',
    '바이어스 사용은 0 또는 1이어야 합니다.': 'Bias flag must be 0 or 1.',
    '종료 여부는 0 또는 1이어야 합니다.': 'Terminal-state flag must be 0 or 1.',
    '정답은 이진 레이블 0 또는 1이어야 합니다.': 'Targets must be binary labels (0 or 1).',
    '예측 확률은 0~1 사이여야 합니다.': 'Predicted probabilities must be within [0, 1].',
    '커널이 입력/패딩보다 큽니다. 출력 크기가 정의되지 않습니다.':
        'Effective kernel is larger than the padded input; output size is undefined.',
    '전이 확률은 모두 0~1이고, 합계는 1이어야 합니다.':
        'Transition probabilities must be within [0, 1] and sum to 1.',
    'W열=x길이, W행=b길이여야 합니다.':
        'W columns must match x length, and W rows must match b length.',
    '데이터 크기가 일치하지 않습니다': 'Data shapes do not match',
    '크기 오류': 'Shape mismatch',
    '모든 행의 열 개수가 같아야 합니다.': 'All matrix rows must have equal lengths.',
    '숫자를 하나 이상 입력하세요.': 'Enter at least one number.',
    'NaN/무한대는 사용할 수 없습니다.': 'NaN and infinity are not allowed.',
    '유효한 숫자를 입력하세요.': 'Enter a valid number.',
    '정수를 입력하세요.': 'Enter an integer.',
    '행을 입력하세요.': 'Enter one or more matrix rows.',
    '범위로 입력하세요.': 'must be within this range.',
    '이상의 정수를 입력하세요.': 'or greater is required (integer).',
    '학습률은 0보다 커야 합니다.': 'Learning rate must be greater than 0.',
    '정답': 'Targets', '예측 확률': 'Predicted probabilities',
    '예측': 'Predictions', '입력 x': 'Input x', '로짓 x': 'Logits x',
    '가중치 행렬': 'Weight matrix', '바이어스 벡터': 'Bias vector',
    '현재 가중치': 'Current weights', '기울기': 'Gradient',
    '입력 뉴런': 'Input neurons', '출력 뉴런': 'Output neurons',
    '바이어스 사용(0/1)': 'Bias (0/1)', '입력 크기': 'Input size',
    '커널 크기': 'Kernel size', '패딩': 'Padding',
    '스트라이드': 'Stride', '딜레이션': 'Dilation',
    '학습률': 'Learning rate', '보상들': 'Rewards',
    '보상': 'Reward', '감가율': 'Discount factor',
    '다음 상태 가치들': 'Next-state values',
    '다음 상태 가치': 'Next-state value',
    '현재 상태 가치': 'Current-state value',
    '종료(0/1)': 'Done (0/1)', '기존 Q': 'Previous Q',
    '다음 상태 Q 값들': 'Next-state Q values',
    '전이 확률들': 'Transition probabilities',
    '결과별 보상': 'Rewards by outcome',
    '행동별 Q 값': 'Action Q values',
    '전이 확률': 'Transition probabilities',
    '탐험률': 'Exploration rate',
    '벡터': 'Vector', '행렬': 'Matrix', '값': 'Value',
    '행': 'row', '열': 'columns',
}


def op_id(operation: Operation) -> str:
    return operation.compute.__name__


def op_title(operation: Operation, lang: str) -> str:
    return operation.title if lang == 'ko' else EN_OPERATIONS[op_id(operation)][0]


def op_description(operation: Operation, lang: str) -> str:
    return operation.description if lang == 'ko' else EN_OPERATIONS[op_id(operation)][1]


def op_formula(operation: Operation, lang: str) -> str:
    return operation.formula if lang == 'ko' else EN_OPERATIONS[op_id(operation)][2]


def field_label(operation: Operation, field: Field, lang: str) -> str:
    return field.label if lang == 'ko' else EN_OPERATIONS[op_id(operation)][3][field.key]


def localized_result(result: object, lang: str) -> str:
    if isinstance(result, dict):
        key_map = RESULT_KEYS_KO if lang == 'ko' else {}
        return '\n'.join(f'{key_map.get(k, k)}: {format_result(v)}' for k, v in result.items())
    return format_result(result)


def localized_error(exc: Exception, lang: str) -> str:
    message = str(exc)
    if lang == 'ko':
        return message
    for ko in sorted(ERROR_EN, key=len, reverse=True):
        message = message.replace(ko, ERROR_EN[ko])
    return message


# ----------------------------- Desktop GUI --------------------------
class CalculatorTab:
    def __init__(self, parent, operations: tuple[Operation, ...], language_getter):
        import tkinter as tk
        from tkinter import ttk, messagebox

        self.tk = tk
        self.ttk = ttk
        self.messagebox = messagebox
        self.operations = operations
        self.language_getter = language_getter
        self.operation_index = 0
        self.saved_values: dict[str, dict[str, str]] = {}
        self.entries: dict[str, object] = {}
        self.input_labels: dict[str, object] = {}
        self.raw_result = None
        self.result_text = ''
        self.output_mode = 'ready'  # ready / result / error
        self.last_error = None
        self.status_mode = 'hint'

        self.frame = ttk.Frame(parent, padding=20)
        self.frame.columnconfigure(0, weight=1)
        self.heading = ttk.Label(self.frame, font=('Malgun Gothic', 12, 'bold'))
        self.heading.grid(row=0, column=0, sticky='w')
        self.selected = tk.StringVar()
        self.chooser = ttk.Combobox(self.frame, textvariable=self.selected,
                                    state='readonly', font=('Malgun Gothic', 12), height=14)
        self.chooser.grid(row=1, column=0, sticky='ew', pady=(5, 12))
        self.chooser.bind('<<ComboboxSelected>>', self.on_choose)

        self.description = ttk.Label(self.frame, font=('Malgun Gothic', 12), wraplength=920)
        self.description.grid(row=2, column=0, sticky='w', pady=(0, 6))
        self.formula = ttk.Label(self.frame, font=('Consolas', 12), wraplength=920)
        self.formula.grid(row=3, column=0, sticky='w', pady=(0, 12))

        self.inputs_frame = ttk.Frame(self.frame)
        self.inputs_frame.grid(row=4, column=0, sticky='ew')
        self.inputs_frame.columnconfigure(1, weight=1)

        buttons = ttk.Frame(self.frame)
        buttons.grid(row=5, column=0, sticky='w', pady=(16, 14))
        self.calculate_button = ttk.Button(buttons, command=self.calculate)
        self.calculate_button.pack(side='left', padx=(0, 9))
        self.reset_button = ttk.Button(buttons, command=self.reset_examples)
        self.reset_button.pack(side='left', padx=(0, 9))
        self.copy_button = ttk.Button(buttons, command=self.copy_result)
        self.copy_button.pack(side='left')

        self.result_label = ttk.Label(self.frame, font=('Malgun Gothic', 12, 'bold'))
        self.result_label.grid(row=6, column=0, sticky='w')
        self.output = tk.Text(self.frame, height=7, wrap='word', font=('Consolas', 13),
                              bg='#F6F8FA', fg='#152238', relief='solid', bd=1)
        self.output.grid(row=7, column=0, sticky='nsew', pady=(6, 8))
        self.output.configure(state='disabled')
        self.frame.rowconfigure(7, weight=1)
        self.status = ttk.Label(self.frame, font=('Malgun Gothic', 10))
        self.status.grid(row=8, column=0, sticky='w')
        self.refresh_language(initial=True)

    @property
    def lang(self) -> str:
        return self.language_getter()

    def tr(self, key: str) -> str:
        return UI[self.lang][key]

    def current_operation(self) -> Operation:
        return self.operations[self.operation_index]

    def save_current_values(self) -> None:
        if self.entries:
            self.saved_values[op_id(self.current_operation())] = {
                key: entry.get() for key, entry in self.entries.items()
            }

    def on_choose(self, _event=None) -> None:
        new_index = self.chooser.current()
        if new_index < 0 or new_index == self.operation_index:
            return
        self.save_current_values()
        self.operation_index = new_index
        self.raw_result = None
        self.last_error = None
        self.result_text = ''
        self.output_mode = 'ready'
        self.status_mode = 'hint'
        self.show_operation()

    def refresh_language(self, initial=False) -> None:
        # Preserve current form values and computed result when toggling language.
        if not initial:
            self.save_current_values()
        self.heading.configure(text=self.tr('select'))
        self.chooser['values'] = [op_title(op, self.lang) for op in self.operations]
        self.chooser.current(self.operation_index)
        self.calculate_button.configure(text=self.tr('calculate'))
        self.reset_button.configure(text=self.tr('reset'))
        self.copy_button.configure(text=self.tr('copy'))
        self.result_label.configure(text=self.tr('result'))
        self.show_operation(preserve_output=not initial)

    def show_operation(self, preserve_output=False) -> None:
        for child in self.inputs_frame.winfo_children():
            child.destroy()
        self.entries.clear()
        self.input_labels.clear()
        op = self.current_operation()
        self.description.configure(text=op_description(op, self.lang))
        self.formula.configure(text=f"{self.tr('formula')}: {op_formula(op, self.lang)}")
        retained = self.saved_values.get(op_id(op), {})
        for i, field in enumerate(op.fields):
            label = self.ttk.Label(self.inputs_frame, text=field_label(op, field, self.lang),
                                   font=('Malgun Gothic', 11))
            label.grid(row=i, column=0, sticky='w', padx=(0, 16), pady=5)
            self.input_labels[field.key] = label
            entry = self.ttk.Entry(self.inputs_frame, font=('Consolas', 12))
            entry.insert(0, retained.get(field.key, field.example))
            entry.grid(row=i, column=1, sticky='ew', pady=5)
            entry.bind('<Return>', lambda _event: self.calculate())
            self.entries[field.key] = entry
        self.show_result_or_hint() if preserve_output else self.write_output(self.tr('ready'))
        self.show_status()

    def reset_examples(self) -> None:
        # Reset only the selected operation, without affecting other saved inputs.
        self.saved_values.pop(op_id(self.current_operation()), None)
        self.raw_result = None
        self.last_error = None
        self.result_text = ''
        self.output_mode = 'ready'
        self.status_mode = 'hint'
        self.show_operation()

    def write_output(self, content: str) -> None:
        self.output.configure(state='normal')
        self.output.delete('1.0', 'end')
        self.output.insert('1.0', content)
        self.output.configure(state='disabled')

    def show_status(self) -> None:
        self.status.configure(text=self.tr(self.status_mode))

    def show_result_or_hint(self) -> None:
        if self.output_mode == 'result' and self.raw_result is not None:
            self.result_text = localized_result(self.raw_result, self.lang)
            self.write_output(self.result_text)
        elif self.output_mode == 'error' and self.last_error is not None:
            self.write_output(f"{self.tr('input_error')}: {localized_error(self.last_error, self.lang)}")
        else:
            self.write_output(self.tr('ready'))

    def calculate(self) -> None:
        try:
            args = {key: widget.get() for key, widget in self.entries.items()}
            result = self.current_operation().compute(args)
            self.raw_result = result
            self.last_error = None
            self.output_mode = 'result'
            self.status_mode = 'calculated'
        except (ValueError, OverflowError, FloatingPointError) as exc:
            self.raw_result = None
            self.last_error = exc
            self.result_text = ''
            self.output_mode = 'error'
            self.status_mode = 'check'
        self.show_result_or_hint()
        self.show_status()

    def copy_result(self) -> None:
        if not self.result_text:
            self.messagebox.showinfo(self.tr('copy'), self.tr('first'))
            return
        self.frame.clipboard_clear()
        self.frame.clipboard_append(self.result_text)
        self.status.configure(text=self.tr('copied'))


def run_gui(initial_language: str = 'ko') -> None:
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.geometry('1080x760')
    root.minsize(760, 650)
    style = ttk.Style(root)
    if 'clam' in style.theme_names():
        style.theme_use('clam')
    style.configure('TButton', font=('Malgun Gothic', 11), padding=(12, 8))
    style.configure('TNotebook.Tab', font=('Malgun Gothic', 12, 'bold'), padding=(20, 10))

    lang = {'code': initial_language}
    header = ttk.Frame(root, padding=(14, 8))
    header.pack(fill='x')
    title = ttk.Label(header, font=('Malgun Gothic', 13, 'bold'))
    title.pack(side='left')
    language_label = ttk.Label(header, font=('Malgun Gothic', 11))
    language_label.pack(side='right', padx=(0, 8))
    chosen = tk.StringVar(value='한국어' if lang['code'] == 'ko' else 'English')
    selector = ttk.Combobox(header, state='readonly', width=12,
                            textvariable=chosen, values=('한국어', 'English'))
    selector.pack(side='right', padx=(0, 14))
    tabs = ttk.Notebook(root)
    tabs.pack(fill='both', expand=True, padx=12, pady=(0, 12))
    tab_widgets = []
    tab_ids = []
    for code, operations in MENU.items():
        widget = CalculatorTab(tabs, operations, lambda: lang['code'])
        tab_widgets.append(widget)
        tab_ids.append(code)
        tabs.add(widget.frame, text=UI[lang['code']]['tab_' + code.lower()])

    def change_language(_event=None):
        lang['code'] = 'en' if chosen.get() == 'English' else 'ko'
        refresh_header()
        for i, widget in enumerate(tab_widgets):
            widget.refresh_language()
            tabs.tab(widget.frame, text=UI[lang['code']]['tab_' + tab_ids[i].lower()])

    def refresh_header():
        title.configure(text=UI[lang['code']]['window'])
        language_label.configure(text=UI[lang['code']]['language'])
        root.title(UI[lang['code']]['window'])

    selector.bind('<<ComboboxSelected>>', change_language)
    refresh_header()
    root.mainloop()


# ----------------------------- Unit tests ---------------------------
# ----------------------------- Original tests ------------------------

class CalculatorTests(unittest.TestCase):
    def test_linear(self):
        self.assertAlmostEqual(ml_linear({'x': '1, 2, 3', 'w': '0.2, 0.4, 0.6', 'b': '0.1'}), 2.9)

    def test_losses(self):
        self.assertAlmostEqual(ml_mse({'y': '1,0,1', 'p': '0.8,0.1,0.6'}), 0.07)
        self.assertAlmostEqual(ml_mae({'y': '1,0,1', 'p': '0.8,0.1,0.6'}), 0.7 / 3)
        self.assertAlmostEqual(ml_bce({'y': '1,0', 'p': '0.9,0.2'}), -(math.log(0.9)+math.log(0.8))/2)

    def test_binary_metrics(self):
        m = ml_binary_metrics({'y': '1,0,1,0,1', 'p': '1,1,1,0,0'})
        self.assertEqual((m['TP'], m['TN'], m['FP'], m['FN']), (2, 1, 1, 1))
        self.assertAlmostEqual(m['F1'], 2/3)

    def test_dl(self):
        np.testing.assert_allclose(dl_sigmoid({'x': '-2,0,2'})[1], 0.5)
        np.testing.assert_array_equal(dl_relu({'x': '-2,0,3'}), [0, 0, 3])
        self.assertAlmostEqual(float(np.sum(dl_softmax({'x': '1,2,3'}))), 1)
        np.testing.assert_allclose(dl_dense({'x': '1,2', 'w': '0.2,0.4;0.6,0.8', 'b': '0.1,-0.1'}), [1.1, 2.1])
        self.assertEqual(dl_params({'ni': '128', 'no': '64', 'bias': '1'})['Total parameters'], 8256)
        self.assertEqual(dl_conv_output({'h': '32', 'k': '3', 'p': '1', 's': '2', 'd': '1'})['Output size (1D)'], 16)
        np.testing.assert_allclose(dl_gradient({'w': '1,2', 'g': '0.1,-0.2', 'lr': '0.01'}), [0.999, 2.002])

    def test_rl(self):
        self.assertAlmostEqual(rl_return({'r': '1,2,3', 'gamma': '0.9'}), 5.23)
        self.assertAlmostEqual(rl_td_target({'r': '1', 'gamma': '.9', 'vnext': '5', 'done': '0'}), 5.5)
        self.assertAlmostEqual(rl_td_target({'r': '1', 'gamma': '.9', 'vnext': '5', 'done': '1'}), 1)
        self.assertAlmostEqual(rl_td_error({'r': '1', 'gamma': '.9', 'vnext': '5', 'current': '4', 'done': '0'})['TD error'], 1.5)
        self.assertAlmostEqual(rl_q_update({'q': '2', 'alpha': '.1', 'r': '1', 'gamma': '.9', 'nextq': '2,4,3', 'done': '0'})['Updated Q'], 2.26)
        self.assertAlmostEqual(rl_bellman_expect({'probs': '.7,.3', 'rewards': '1,-1', 'values': '4,2', 'gamma': '.9'}), 3.46)
        np.testing.assert_allclose(rl_epsilon_greedy({'q': '2,5,5,1', 'eps': '0.1'})['Action selection probabilities'], [0.025, 0.475, 0.475, 0.025])

    def test_reject_invalid(self):
        with self.assertRaises(ValueError):
            ml_mse({'y': '1, 2', 'p': '1'})
        with self.assertRaises(ValueError):
            rl_bellman_expect({'probs': '.7,.4', 'rewards': '1,2', 'values': '3,4', 'gamma': '.9'})
        with self.assertRaises(ValueError):
            integer('2.5')



class BilingualTests(unittest.TestCase):
    def test_all_operations_have_complete_english_translation(self):
        names = [op_id(op) for group in MENU.values() for op in group]
        self.assertEqual(len(names), 19)
        self.assertEqual(set(names), set(EN_OPERATIONS))
        for op in (op for group in MENU.values() for op in group):
            title, description, formula, field_map = EN_OPERATIONS[op_id(op)]
            self.assertTrue(title and description and formula)
            self.assertEqual(set(field_map), {f.key for f in op.fields})
            for field in op.fields:
                self.assertTrue(field_label(op, field, 'en'))
                self.assertTrue(field_label(op, field, 'ko'))

    def test_localized_result_and_error(self):
        result = dl_params({'ni': '3', 'no': '2', 'bias': '1'})
        self.assertIn('Total parameters', localized_result(result, 'en'))
        self.assertIn('총 파라미터 수', localized_result(result, 'ko'))
        self.assertIn('Enter an integer', localized_error(ValueError('값: 정수를 입력하세요.'), 'en'))
        self.assertEqual(localized_error(ValueError('입력 오류'), 'ko'), '입력 오류')

    def test_original_compute_unchanged(self):
        self.assertEqual(ml_linear({'x': '1,2', 'w': '3,4', 'b': '5'}), 16.0)
        self.assertAlmostEqual(sum(rl_epsilon_greedy({'q': '1, 3, 2', 'eps': '.2'})
                                   ['Action selection probabilities']), 1)

if __name__ == '__main__':
    if '--test' in sys.argv:
        suite = unittest.TestSuite([
            unittest.defaultTestLoader.loadTestsFromTestCase(CalculatorTests),
            unittest.defaultTestLoader.loadTestsFromTestCase(BilingualTests),
        ])
        outcome = unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit(0 if outcome.wasSuccessful() else 1)
    args = sys.argv[1:]
    language = 'ko'
    if '--lang' in args:
        i = args.index('--lang')
        if i + 1 >= len(args) or args[i + 1] not in ('ko', 'en'):
            sys.exit('Usage: python ml_dl_rl_calculator_bilingual.py [--lang ko|en] [--test]')
        language = args[i + 1]
        del args[i:i + 2]
    elif any(arg.startswith('--lang=') for arg in args):
        val = next(a.split('=', 1)[1] for a in args if a.startswith('--lang='))
        if val not in ('ko', 'en'):
            sys.exit('Language must be ko or en.')
        language = val
        args = [a for a in args if not a.startswith('--lang=')]
    if args:
        sys.exit('Usage: python ml_dl_rl_calculator_bilingual.py [--lang ko|en] [--test]')
    run_gui(language)
