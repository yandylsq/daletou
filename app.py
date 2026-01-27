from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import pandas as pd
import numpy as np
from datetime import datetime
import pickle
import os
import json
from model_engine import DaletouPredictor

app = Flask(__name__)
CORS(app)

# 初始化预测器
predictor = DaletouPredictor()

# 任务状态追踪
active_tasks = set()

@app.route('/api/cancel', methods=['POST'])
def cancel_task():
    data = request.json
    task_id = data.get('task_id')
    if task_id in active_tasks:
        active_tasks.remove(task_id)
        return jsonify({'success': True, 'message': '任务已发送取消信号'})
    return jsonify({'success': False, 'message': '未找到活跃任务'})

def is_task_cancelled(task_id):
    """检查任务是否已被用户取消"""
    return task_id not in active_tasks

def load_full_history():
    """从本地文件加载完整历史数据供预测引擎使用"""
    local_file = 'daletou_history_full.txt'
    if os.path.exists(local_file):
        try:
            with open(local_file, 'r', encoding='utf-8') as f:
                data = f.read()
                if len(data.strip()) > 1000: # 简单校验数据量
                    return data
        except Exception as e:
            print(f"读取完整历史数据文件失败: {e}")
    return HISTORICAL_DATA

# 历史数据（备用/少量）
HISTORICAL_DATA = """25150	2025-12-31 13 14 15 28 31-01 05
25149	2025-12-29	24 26 30 31 32-05 12
25148	2025-12-27	03 04 14 30 32-08 12
25147	2025-12-24	06 16 21 25 33-07 08
25146	2025-12-22	06 11 13 16 22-02 03
25145	2025-12-20	05 07 20 22 25-04 05
25144	2025-12-17	02 05 13 15 28-05 08
25143	2025-12-15	03 04 18 24 29-07 12
25142	2025-12-13	09 10 14 27 29-02 09
25141	2025-12-10	04 09 24 28 29-02 10
25140	2025-12-08	04 05 13 18 34-02 08
25139	2025-12-06	08 18 22 30 35-01 04
25138	2025-12-03	01 	03 19 21 23-07 11
25137	2025-11-29	07	08	09	11	22-05	11
25136	2025-11-29	07	11	15	16	23-09	11
25135	2025-11-26	02	10	16	28	32-01	07
25134	2025-11-24	07	12	18	27	33-09	10
25133	2025-11-22	04	11	23	27	35-07	11
25132	2025-11-19	01	09	10	12	19-06	07
25131	2025-11-17	03	08	25	29	32-09	12
25130	2025-11-15	01	13	16	27	29-02	11
25129	2025-11-12	03	09	14	28	35-02	04
25128	2025-11-10	03	06	26	30	33-11	12
25127	2025-11-08	04	05	19	28	29-05	08
25126	2025-11-05	01	08	18	27	30-06	07
25125	2025-11-03	10	11	13	19	35-04	11
25124	2025-11-01	06	09	14	26	27-08	09
25123	2025-10-29	08	13	24	25	31-04	10
25122	2025-10-27	02	03	06	16	17-04	05
25121	2025-10-25	02	03	08	13	21-07	12
25120	2025-10-22	11	13	22	26	35-02	08
25119	2025-10-20	08	15	27	29	31-01	07
25118	2025-10-18	02	08	09	12	21-04	05
25117	2025-10-15	05	10	18	21	29-05	07
25116	2025-10-13	02	06	16	22	29-08	12
25115	2025-10-11	03	12	14	21	35-01	05
25114	2025-10-08	03	08	09	12	16-01	05
25113	2025-10-06	01	14	18	28	35-02	03
25112	2025-09-29	03	04	21	23	24-09	12
25111	2025-09-27	02	09	14	21	26-02	12
25110	2025-09-24	01	15	22	30	31-02	08
25109	2025-09-22	04	08	10	13	26-09	10
25108	2025-09-20	14	18	21	24	29-03	06
25107	2025-09-17	05	07	08	15	33-06	10
25106	2025-09-15	05	06	11	26	29-05	10
25105	2025-09-13	15	16	25	28	34-10	12
25104	2025-09-10	02	06	09	22	34-02	08
25103	2025-09-08	05	08	19	32	34-04	05
25102	2025-09-06	09	10	13	26	28-02	04
25101	2025-09-03	05	07	19	26	32-08	09
25100	2025-09-01	26 	28	32 	34	35-02	07
25099	2025-08-30	06	12	20	26	31-02	04
25098	2025-08-27	01	07	09	10	23-10	12
25097	2025-08-25	05	24	25	32	34-01	09
25096	2025-08-23	02	11	17	22	24-07	09
25095	2025-08-20	07	13	14	19	27-06	10
25094	2025-08-18	04	09	17	30	33-05	09
25093	2025-08-16	01	07	09	16	30-02	05
25092	2025-08-13	04	10	17	25	32-05	07
25091	2025-08-11	01	19	22	25	27-03	10
25090	2025-08-09	06	14	19	22	27-01	04
25089	2025-08-06	02	11	12	32	34-03	10	
25088	2025-08-04	08	09	10	11	35-05	11	
25087	2025-08-02	05	13	14	16	20-03	08	
25086	2025-07-30	02	06	23	24	33-01	10	
25085	2025-07-28	02	05	09	14	33-04	09	
25084	2025-07-26	09	11	13	18	29-04	11	
25083	2025-07-23	12	17	18	20	34-02	05	
25082	2025-07-21	02	03	04	12	26-01	08	
25081	2025-07-19	01	04	06	15	18-02	03	
25080	2025-07-16	09	10	18	22	24-03	12"""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """生成预测 (流式实时响应版)"""
    data = request.json or {}
    task_id = data.get('task_id', 'default_predict')
    active_tasks.add(task_id)
    
    period = data.get('period', '')
    kill_red = data.get('kill_red', [])
    kill_blue = data.get('kill_blue', [])
    sum_min = data.get('sum_min')
    sum_max = data.get('sum_max')
    odd_even_ratio = data.get('odd_even_ratio')
    reference_urls = data.get('reference_urls', [])

    def generate():
        try:
            print(f"[DEBUG] 预测任务开始 - task_id: {task_id}, period: {period}", flush=True)
            
            if not predictor.is_trained:
                print(f"[ERROR] 模型未训练", flush=True)
                yield f"data: {json.dumps({'type': 'error', 'error': '模型未训练', 'need_training': True})}\n\n"
                return

            sum_range = [int(sum_min), int(sum_max)] if sum_min is not None and sum_max is not None else None
            
            # --- 模拟流式预测 ---
            # 1. 发送开始信号和基础信息
            actual_data = None
            if predictor.history_df is not None:
                try:
                    hist_row = predictor.history_df[predictor.history_df['period'] == int(period)]
                    if not hist_row.empty:
                        actual_data = {'red': hist_row.iloc[0]['red'], 'blue': hist_row.iloc[0]['blue']}
                except Exception as e:
                    print(f"[WARN] 获取历史数据失败: {e}", flush=True)

            print(f"[DEBUG] 发送 start 信号", flush=True)
            yield f"data: {json.dumps({'type': 'start', 'period': period, 'actual_data': actual_data})}\n\n"

            # 2. 调用预测引擎 (Generator 模式)
            print(f"[DEBUG] 开始调用 predictor.predict", flush=True)
            pred_count = 0
            for pred in predictor.predict(
                period=period, kill_red=kill_red, kill_blue=kill_blue,
                n_combinations=20, sum_range=sum_range,
                odd_even_ratio=odd_even_ratio, reference_urls=reference_urls,
                cancel_check=lambda: is_task_cancelled(task_id)
            ):
                if is_task_cancelled(task_id):
                    print(f"[INFO] 任务被取消", flush=True)
                    break
                pred_count += 1
                print(f"[DEBUG] 产出第 {pred_count} 组预测", flush=True)
                yield f"data: {json.dumps({'type': 'prediction_item', 'prediction': pred})}\n\n"
            
            print(f"[DEBUG] 预测完成，共产出 {pred_count} 组", flush=True)

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[ERROR] 预测异常: {e}\n{error_detail}", flush=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'detail': error_detail})}\n\n"
        finally:
            if task_id in active_tasks: active_tasks.remove(task_id)
            print(f"[DEBUG] 发送 done 信号", flush=True)
            yield f"data: {json.dumps({'type': 'done', 'model_info': predictor.get_model_info()})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

def get_next_period(history_str):
    """根据历史数据计算下一期号 - 增强版"""
    try:
        import re
        periods = []
        for line in history_str.strip().split('\n'):
            # 匹配 5 位连续数字作为期号
            match = re.search(r'(\d{5})', line)
            if match:
                periods.append(int(match.group(1)))
        
        if not periods:
            return "26008" # 如果解析失败，根据当前时间线返回一个合理的默认值
            
        latest_period = max(periods)
        
        # 处理跨年逻辑 (YYNNN)
        year = latest_period // 1000
        num = latest_period % 1000
        
        # 简单加 1，大多数情况适用
        next_val = latest_period + 1
        return str(next_val).zfill(5)
    except:
        return "26008"

@app.route('/api/history', methods=['GET'])
def get_history():
    """获取历史开奖数据 - 仅加载数据，不训练模型"""
    try:
        full_data = load_full_history()
        # 仅解析数据，不训练模型（避免首次加载耗时）
        if predictor.history_df is None:
            predictor.history_df = predictor.parse_historical_data(full_data)
            
        history = predictor.get_history_data()
        
        # 优先从已加载的数据中获取最新期号
        if predictor.history_df is not None and not predictor.history_df.empty:
            latest_p = int(predictor.history_df['period'].max())
            next_period = str(latest_p + 1).zfill(5)
        else:
            next_period = get_next_period(full_data)
        
        return jsonify({
            'success': True,
            'data': history,
            'next_period': next_period,
            'model_trained': predictor.is_trained  # 返回模型训练状态
        })
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/train', methods=['POST'])
def train_model():
    """训练所有模型"""
    try:
        if predictor.is_trained:
            return jsonify({
                'success': True,
                'message': '模型已经训练完成',
                'model_info': predictor.get_model_info()
            })
        
        full_data = load_full_history()
        predictor.train(full_data, train_ensemble=True)
        
        return jsonify({
            'success': True,
            'message': '模型训练完成！',
            'model_info': predictor.get_model_info()
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(error_detail)
        return jsonify({'success': False, 'error': str(e), 'detail': error_detail}), 500

@app.route('/api/validate', methods=['POST'])
def validate():
    """验证预测准确率 (深度流式响应版)"""
    data = request.json or {}
    task_id = data.get('task_id', 'default_val')
    active_tasks.add(task_id)
    
    start_period = data.get('start_period', '25080')
    end_period = data.get('end_period', '25150')

    def generate():
        try:
            if not predictor.is_trained:
                yield f"data: {json.dumps({'error': '模型未训练', 'need_training': True})}\n\n"
                return

            val_data = predictor.history_df[(predictor.history_df['period'] >= int(start_period)) & (predictor.history_df['period'] <= int(end_period))].copy()
            
            # 使用临时的子预测器进行回测
            sub_predictor = DaletouPredictor()
            from collections import Counter
            hits_dist = Counter()
            total_red_hits = 0
            total_blue_hits = 0
            count = 0

            for i, row in val_data.iterrows():
                if is_task_cancelled(task_id): break
                
                p = row['period']
                act_r = row['red']
                act_b = row['blue']
                train_df = predictor.history_df[predictor.history_df['period'] < p]
                
                # 快速预测逻辑
                sub_predictor.history_df = train_df
                sub_predictor.is_trained = True
                sub_predictor._build_markov_chain()
                sub_predictor._learn_patterns()
                sub_predictor._init_dynamic_weights()
                sub_predictor.load_state(tag=str(p)) # 尝试加载
                
                preds = list(sub_predictor.predict(str(p), n_combinations=20, is_backtest=True))
                if not preds: continue
                
                count += 1
                best_pred = preds[0]
                r_hits = len(set(act_r) & set(best_pred['red']))
                b_hits = len(set(act_b) & set(best_pred['blue']))
                total_red_hits += r_hits
                total_blue_hits += b_hits
                
                # 统计最高命中用于覆盖率
                br, bb = 0, 0
                for pr in preds:
                    hr = len(set(act_r) & set(pr['red']))
                    hb = len(set(act_b) & set(pr['blue']))
                    if hr > br or (hr == br and hb > bb): br, bb = hr, hb
                hits_dist[f"R{br}+B{bb}"] += 1
                
                # 构建结果项
                res_item = {
                    'type': 'period_result',
                    'period': str(p),
                    'actual_red': act_r,
                    'actual_blue': act_b,
                    'predicted_red': best_pred['red'],
                    'predicted_blue': best_pred['blue'],
                    'red_hits': r_hits,
                    'blue_hits': b_hits,
                    'reason': best_pred.get('reason', ''),
                    'current_avg_red': round(total_red_hits / count, 2),
                    'current_avg_blue': round(total_blue_hits / count, 2),
                    'current_core_cov': sub_predictor._calc_temp_coverage(hits_dist, count)
                }
                yield f"data: {json.dumps(res_item)}\n\n"

        except Exception as e:
            import traceback
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'detail': traceback.format_exc()})}\n\n"
        finally:
            if task_id in active_tasks: active_tasks.remove(task_id)
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/api/export', methods=['POST'])
def export_combinations():
    """导出过滤后的号码组合"""
    task_id = request.json.get('task_id', 'default_export')
    active_tasks.add(task_id)
    try:
        from export_combinations import DaletouExporter
        
        # 获取参数
        data = request.json or {}
        # ... (保持参数获取逻辑不变)
        kill_red = data.get('kill_red', [])
        kill_blue = data.get('kill_blue', [])
        sum_min = data.get('sum_min')
        sum_max = data.get('sum_max')
        odd_even_ratio = data.get('odd_even_ratio')
        
        # 处理和值范围
        sum_range = None
        if sum_min is not None and sum_max is not None:
            sum_range = [int(sum_min), int(sum_max)]
        
        exporter = DaletouExporter()
        # 传入任务检查函数
        filtered_count = exporter.export_filtered_combinations(
            kill_red=kill_red,
            kill_blue=kill_blue,
            sum_range=sum_range,
            odd_even_ratio=odd_even_ratio,
            cancel_check=lambda: is_task_cancelled(task_id)
        )
        
        if filtered_count is None: # 表示被中途停止
            return jsonify({'success': False, 'error': '任务已由用户终止'})

        return jsonify({
            'success': True,
            'filtered_count': filtered_count,
            'message': f'导出完成！共生成{filtered_count:,}组过滤后的号码组合',
            'export_dir': 'exports',
            'kill_red': kill_red,
            'kill_blue': kill_blue,
            'sum_range': sum_range,
            'odd_even_ratio': odd_even_ratio
        })
    except Exception as e:
        # ... (错误处理逻辑)
        import traceback
        error_detail = traceback.format_exc()
        return jsonify({
            'success': False, 
            'error': str(e),
            'detail': error_detail
        }), 500
    finally:
        if task_id in active_tasks:
            active_tasks.remove(task_id)

@app.route('/api/query', methods=['POST'])
def query_combination():
    """查询号码组合是否在过滤后的列表中"""
    task_id = request.json.get('task_id', 'default_query')
    active_tasks.add(task_id)
    try:
        from export_combinations import DaletouExporter
        
        # 获取参数
        data = request.json or {}
        # ... (参数获取逻辑保持不变)
        red_numbers = data.get('red_numbers', [])
        blue_numbers = data.get('blue_numbers', [])
        kill_red = data.get('kill_red', [])
        kill_blue = data.get('kill_blue', [])
        sum_min = data.get('sum_min')
        sum_max = data.get('sum_max')
        odd_even_ratio = data.get('odd_even_ratio')
        
        # 验证输入
        if len(red_numbers) != 5 or len(blue_numbers) != 2:
            return jsonify({
                'success': False,
                'error': '请输入5个前区号码和2个后区号码'
            }), 400
        
        # 验证号码范围
        if not all(1 <= n <= 35 for n in red_numbers):
            return jsonify({
                'success': False,
                'error': '前区号码必须在1-35之间'
            }), 400
        
        if not all(1 <= n <= 12 for n in blue_numbers):
            return jsonify({
                'success': False,
                'error': '后区号码必须在1-12之间'
            }), 400
        
        # 处理和值范围
        sum_range = None
        if sum_min is not None and sum_max is not None:
            sum_range = [int(sum_min), int(sum_max)]
        
        # 构建查询的组合
        query_combo = tuple(sorted(red_numbers)) + tuple(sorted(blue_numbers))
        
        # 获取过滤后的组合
        exporter = DaletouExporter()
        result = exporter.get_filtered_combinations(
            kill_red=kill_red,
            kill_blue=kill_blue,
            sum_range=sum_range,
            odd_even_ratio=odd_even_ratio,
            cancel_check=lambda: is_task_cancelled(task_id)
        )
        
        if result is None:
            return jsonify({'success': False, 'error': '查询已取消'})
            
        filtered_combos = result['filtered_combos']
        is_in_filtered = query_combo in filtered_combos
        
        # 计算奇偶比
        odd_count = sum(1 for n in red_numbers if n % 2 == 1)
        even_count = 5 - odd_count
        ratio_str = f"{odd_count}:{even_count}"
        
        # 格式化组合字符串
        combo_str = f"{red_numbers[0]:02d} {red_numbers[1]:02d} {red_numbers[2]:02d} {red_numbers[3]:02d} {red_numbers[4]:02d}-{blue_numbers[0]:02d} {blue_numbers[1]:02d}"
        
        return jsonify({
            'success': True,
            'is_in_filtered': is_in_filtered,
            'combination': combo_str,
            'red_sum': sum(red_numbers),
            'odd_even_ratio': ratio_str,
            'total_filtered': len(filtered_combos),
            'message': '该组合在过滤后的列表中' if is_in_filtered else '该组合不在过滤后的列表中（已被过滤）'
        })
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return jsonify({
            'success': False, 
            'error': str(e),
            'detail': error_detail
        }), 500
    finally:
        if task_id in active_tasks:
            active_tasks.remove(task_id)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
