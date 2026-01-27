// API 基础地址
const API_BASE = '';

// 全局状态管理
let isPrediciting = false;
let isValidating = false;
let isExporting = false;
let activeTaskIds = {
    'predict': null,
    'validate': null,
    'export': null,
    'query': null
};
let modelTrained = false;  // 模型训练状态

/**
 * 更新模型状态显示
 */
function updateModelStatus(trained) {
    modelTrained = trained;
    const statusText = document.getElementById('modelStatusText');
    const trainBtn = document.getElementById('trainModelBtn');
    
    if (trained) {
        statusText.textContent = '✅ 已训练';
        statusText.style.color = '#27ae60';
        trainBtn.style.display = 'none';
    } else {
        statusText.textContent = '⚠️ 未训练';
        statusText.style.color = '#e67e22';
        trainBtn.style.display = 'inline-block';
    }
}

/**
 * 训练所有模型
 */
async function trainModel() {
    const trainBtn = document.getElementById('trainModelBtn');
    const progressSpan = document.getElementById('trainProgress');
    
    // 禁用按钮
    trainBtn.disabled = true;
    trainBtn.textContent = '训练中...';
    progressSpan.style.display = 'inline';
    progressSpan.textContent = '⚙️ 正在训练所有模型，预计需要 30-60 秒，请耐心等待...';
    
    try {
        const response = await fetch(`${API_BASE}/api/train`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateModelStatus(true);
            progressSpan.style.display = 'none';
            alert('✅ ' + data.message + '\n\n现在可以使用预测和回测功能了！');
        } else {
            alert('❌ 模型训练失败：' + data.error);
            trainBtn.disabled = false;
            trainBtn.textContent = '🚀 训练所有模型';
            progressSpan.style.display = 'none';
        }
    } catch (error) {
        alert('❌ 网络错误：' + error.message);
        trainBtn.disabled = false;
        trainBtn.textContent = '🚀 训练所有模型';
        progressSpan.style.display = 'none';
    }
}

/**
 * 切换停止按钮的显示状态
 */
function toggleStopButton(section, show) {
    let btnId = '';
    if (section === 'validate') {
        btnId = 'stopValidateBtn';
    } else {
        btnId = 'stopPredictBtn';
    }
    
    const stopBtn = document.getElementById(btnId);
    if (stopBtn) {
        stopBtn.style.display = show ? 'inline-block' : 'none';
    }
}

/**
 * 停止指定部分正在执行的任务
 */
async function stopTask(section) {
    const taskId = activeTaskIds[section];
    if (!taskId) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/cancel`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: taskId })
        });
        const data = await response.json();
        if (data.success) {
            console.log(`[${section}] 停止信号已发送`);
            toggleStopButton(section, false);
            activeTaskIds[section] = null;
        }
    } catch (error) {
        console.error(`停止任务 ${section} 失败:`, error);
    }
}

// 预测号码 (流式版)
async function predict() {
    if (isPrediciting) return;
    
    const period = document.getElementById('exportPeriod').value;
    const killRedInput = document.getElementById('exportKillRed').value.trim();
    const killBlueInput = document.getElementById('exportKillBlue').value.trim();
    const sumMinInput = document.getElementById('exportSumMin').value.trim();
    const sumMaxInput = document.getElementById('exportSumMax').value.trim();
    const oddEvenRatio = document.getElementById('exportOddEvenRatio').value.trim();
    const referenceUrls = document.getElementById('referenceUrls').value.trim();
    
    if (!period) { alert('请输入期号'); return; }
    
    const killRed = killRedInput ? killRedInput.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) : [];
    const killBlue = killBlueInput ? killBlueInput.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) : [];
    let sumMin = sumMinInput ? parseInt(sumMinInput) : null;
    let sumMax = sumMaxInput ? parseInt(sumMaxInput) : null;
    
    isPrediciting = true;
    const predictBtn = document.querySelector('.export-section .btn-primary');
    const originalText = predictBtn.textContent;
    predictBtn.disabled = true;
    predictBtn.textContent = '预测中...';
    
    document.getElementById('loading').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('predictions').innerHTML = '';
    
    const taskId = 'predict_' + Date.now();
    activeTaskIds['predict'] = taskId;
    toggleStopButton('predict', true);
    
    let actualData = null;

    try {
        await streamFetch(`${API_BASE}/api/predict`, {
            task_id: taskId, period: period, kill_red: killRed, kill_blue: killBlue,
            sum_min: sumMin, sum_max: sumMax, odd_even_ratio: oddEvenRatio,
            reference_urls: referenceUrls ? referenceUrls.split('\n').map(u => u.trim()).filter(u => u) : []
        }, (data) => {
            if (data.type === 'start') {
                actualData = data.actual_data;
                document.getElementById('resultPeriod').textContent = `预测期号：${data.period}`;
                document.getElementById('resultsSection').style.display = 'block';
            } else if (data.type === 'prediction_item') {
                appendSinglePrediction(data.prediction, actualData);
                document.getElementById('resultCount').textContent = `生成组合数：${document.querySelectorAll('.prediction-item').length}`;
            } else if (data.type === 'done') {
                if (data.model_info) displayModelInfo(data.model_info);
            }
        }, () => {
            finalizePredict();
        }, (error) => {
            alert('预测中止: ' + error.message);
            finalizePredict();
        });
    } catch (error) {
        alert('网络错误: ' + error.message);
        finalizePredict();
    }

    function finalizePredict() {
        document.getElementById('loading').style.display = 'none';
        toggleStopButton('predict', false);
        activeTaskIds['predict'] = null;
        isPrediciting = false;
        predictBtn.disabled = false;
        predictBtn.textContent = originalText;
    }
}

function appendSinglePrediction(pred, actualData) {
    const container = document.getElementById('predictions');
    const item = document.createElement('div');
    
    // 根据类型设置不同样式
    if (pred.type === 'compound') {
        item.className = 'prediction-item compound-item';
    } else {
        item.className = 'prediction-item';
    }
    
    // 命中计算（仅对单式号码）
    const actualRedSet = actualData ? new Set(actualData.red) : null;
    const actualBlueSet = actualData ? new Set(actualData.blue) : null;
    
    let hitHtml = '';
    if (actualData && pred.type !== 'compound') {
        const rHits = pred.red.filter(n => actualRedSet.has(n)).length;
        const bHits = pred.blue.filter(n => actualBlueSet.has(n)).length;
        hitHtml = `<span class="hit-badge ${rHits >= 3 ? 'good' : ''} ${rHits >= 4 ? 'excellent' : ''}" style="margin-left:10px;">命中：前区 ${rHits} | 后区 ${bHits}</span>`;
    }

    // 复试号码显示注数
    let compoundCountHtml = '';
    if (pred.type === 'compound' && pred.combination_count) {
        compoundCountHtml = `<span class="compound-count" style="margin-left:10px;color:#e67e22;font-weight:bold;">包含 ${pred.combination_count} 注</span>`;
    }

    const typeLabel = pred.type === 'compound' ? '复试' : '单式';
    const rankLabel = pred.type === 'compound' ? `${typeLabel} #${pred.rank}` : `推荐度 #${pred.rank}`;

    item.innerHTML = `
        <div class="prediction-header">
            <span class="rank-badge ${pred.type === 'compound' ? 'compound-badge' : ''}">${rankLabel}</span>
            <span class="score-badge">评分：${pred.score}</span>
            ${hitHtml}
            ${compoundCountHtml}
        </div>
        <div class="numbers-display">
            <div class="red-balls">${pred.red.map(n => `<div class="ball red-ball" style="${actualRedSet && actualRedSet.has(n) ? 'border:2px solid gold;box-shadow:0 0 8px gold;' : ''}">${String(n).padStart(2,'0')}</div>`).join('')}</div>
            <span class="separator">+</span>
            <div class="blue-balls">${pred.blue.map(n => `<div class="ball blue-ball" style="${actualBlueSet && actualBlueSet.has(n) ? 'border:2px solid gold;box-shadow:0 0 8px gold;' : ''}">${String(n).padStart(2,'0')}</div>`).join('')}</div>
        </div>
        ${pred.reason ? `<div class="prediction-reason" style="margin-top:10px;padding:8px;background:#f9f9f9;border-left:4px solid ${pred.type === 'compound' ? '#e67e22' : '#3498db'};font-size:0.85em;"><strong>🎯 评分理由：</strong><br>${pred.reason.split(' | ').join('<br>• ')}</div>` : ''}
    `;
    container.appendChild(item);
    item.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function displayModelInfo(info) {
    const modelInfo = document.getElementById('modelInfo');
    modelInfo.innerHTML = `
        <h3>📈 模型信息</h3>
        <p><strong>状态：</strong>${info.status}</p>
        <p><strong>训练数据：</strong>共 ${info.history_count} 期</p>
        <p><strong>最新期号：</strong>${info.latest_period}</p>
    `;
}

// 加载历史数据
async function loadHistory() {
    const historyContainer = document.getElementById('historyData');
    historyContainer.innerHTML = '<div style="text-align: center; padding: 20px;">加载中...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/history`);
        const data = await response.json();
        
        if (data.success) {
            const historyList = data.data;
            
            // 更新模型状态
            updateModelStatus(data.model_trained || false);
            
            // 自动填充回测范围：取历史数据中最后 7 期
            if (historyList && historyList.length > 0) {
                const endPeriodInput = document.getElementById('endPeriod');
                const startPeriodInput = document.getElementById('startPeriod');
                
                const latestRecord = historyList[historyList.length - 1];
                const startIdx = Math.max(0, historyList.length - 7);
                const startRecord = historyList[startIdx];
                
                if (endPeriodInput) {
                    endPeriodInput.value = latestRecord.period;
                }
                if (startPeriodInput) {
                    startPeriodInput.value = startRecord.period;
                }
            }

            displayHistory(data.data); // 注意：此函数内部会反转数组
            
            // 自动填充预测目标期号
            if (data.next_period) {
                const periodInput = document.getElementById('exportPeriod');
                if (periodInput) {
                    periodInput.value = data.next_period;
                }
            }
        } else {
            historyContainer.innerHTML = '<div style="text-align: center; padding: 20px; color: red;">加载失败</div>';
        }
    } catch (error) {
        historyContainer.innerHTML = '<div style="text-align: center; padding: 20px; color: red;">网络错误</div>';
    }
}

// 显示历史数据
function displayHistory(historyData) {
    const historyContainer = document.getElementById('historyData');
    historyContainer.innerHTML = '';
    
    if (historyData.length === 0) {
        historyContainer.innerHTML = '<div style="text-align: center; padding: 20px; color: #999;">暂无数据</div>';
        return;
    }
    
    // 倒序显示（最新的在前）
    historyData.reverse().forEach(item => {
        const historyItem = document.createElement('div');
        historyItem.className = 'history-item';
        
        const info = document.createElement('div');
        info.style.display = 'flex';
        info.style.gap = '20px';
        info.style.alignItems = 'center';
        
        const periodSpan = document.createElement('span');
        periodSpan.className = 'history-period';
        periodSpan.textContent = item.period;
        
        const dateSpan = document.createElement('span');
        dateSpan.className = 'history-date';
        dateSpan.textContent = item.date;
        
        info.appendChild(periodSpan);
        info.appendChild(dateSpan);
        
        const numbersDisplay = document.createElement('div');
        numbersDisplay.className = 'numbers-display';
        numbersDisplay.style.flex = '1';
        
        // 红球
        const redBalls = document.createElement('div');
        redBalls.className = 'red-balls';
        item.red.forEach(num => {
            const ball = document.createElement('div');
            ball.className = 'ball red-ball';
            ball.style.width = '35px';
            ball.style.height = '35px';
            ball.style.fontSize = '0.9em';
            ball.textContent = String(num).padStart(2, '0');
            redBalls.appendChild(ball);
        });
        
        // 分隔符
        const separator = document.createElement('span');
        separator.className = 'separator';
        separator.textContent = '+';
        
        // 蓝球
        const blueBalls = document.createElement('div');
        blueBalls.className = 'blue-balls';
        item.blue.forEach(num => {
            const ball = document.createElement('div');
            ball.className = 'ball blue-ball';
            ball.style.width = '35px';
            ball.style.height = '35px';
            ball.style.fontSize = '0.9em';
            ball.textContent = String(num).padStart(2, '0');
            blueBalls.appendChild(ball);
        });
        
        numbersDisplay.appendChild(redBalls);
        numbersDisplay.appendChild(separator);
        numbersDisplay.appendChild(blueBalls);
        
        historyItem.appendChild(info);
        historyItem.appendChild(numbersDisplay);
        historyContainer.appendChild(historyItem);
    });
}

// 回测验证 (重构为流式版)
async function validateModel() {
    if (isValidating) return;
    
    const startPeriod = document.getElementById('startPeriod').value.trim();
    const endPeriod = document.getElementById('endPeriod').value.trim();
    if (!startPeriod || !endPeriod) { alert('请输入起始和结束期号'); return; }
    
    isValidating = true;
    const validateBtn = document.querySelector('.validate-section .btn-primary');
    const originalText = validateBtn.textContent;
    validateBtn.disabled = true;
    validateBtn.textContent = '回测中...';
    
    document.getElementById('validateLoading').style.display = 'block';
    const resultsContainer = document.getElementById('validateResults');
    resultsContainer.innerHTML = '<div id="liveStats" class="validate-summary">正在初始化实时统计...</div><div id="liveItems"></div>';
    
    const taskId = 'validate_' + Date.now();
    activeTaskIds['validate'] = taskId;
    toggleStopButton('validate', true);
    
    await streamFetch(`${API_BASE}/api/validate`, {
        task_id: taskId, start_period: startPeriod, end_period: endPeriod
    }, (data) => {
        if (data.type === 'period_result') {
            updateLiveStats(data);
            appendLiveValidateItem(data);
        }
    }, () => {
        finalizeValidate();
    }, (err) => {
        alert('回测中止: ' + err.message);
        finalizeValidate();
    });

    function finalizeValidate() {
        document.getElementById('validateLoading').style.display = 'none';
        toggleStopButton('validate', false);
        activeTaskIds['validate'] = null;
        isValidating = false;
        validateBtn.disabled = false;
        validateBtn.textContent = originalText;
    }
}

function updateLiveStats(data) {
    const statsDiv = document.getElementById('liveStats');
    statsDiv.innerHTML = `
        <h3>📊 实时回测统计 (第 ${data.period} 期)</h3>
        <div class="summary-stats">
            <div class="stat-item"><div class="stat-value">${data.current_avg_red}</div><div class="stat-label">平均红球命中</div></div>
            <div class="stat-item"><div class="stat-value">${data.current_avg_blue}</div><div class="stat-label">平均蓝球命中</div></div>
            <div class="stat-item"><div class="stat-value">${data.current_core_cov.toFixed(1)}%</div><div class="stat-label">核心覆盖率</div></div>
        </div>
    `;
}

function appendLiveValidateItem(result) {
    const container = document.getElementById('liveItems');
    const item = document.createElement('div');
    item.className = 'validate-item anim-fade-in';
    
    let badgeClass = 'hit-badge';
    if (result.red_hits >= 3) badgeClass += ' good';
    if (result.red_hits >= 4) badgeClass += ' excellent';
    
    item.innerHTML = `
        <div class="validate-header">
            <span class="period-title">第 ${result.period} 期</span>
            <span class="${badgeClass}">前区 ${result.red_hits}/5 | 后区 ${result.blue_hits}/2</span>
        </div>
        <div class="compare-row">
            <div class="compare-col">
                <h4>🎲 实际开奖</h4>
                <div class="numbers-display">
                    <div class="red-balls">${result.actual_red.map(n => `<div class="ball red-ball" style="width:35px;height:35px;">${String(n).padStart(2,'0')}</div>`).join('')}</div>
                    <span class="separator">+</span>
                    <div class="blue-balls">${result.actual_blue.map(n => `<div class="ball blue-ball" style="width:35px;height:35px;">${String(n).padStart(2,'0')}</div>`).join('')}</div>
                </div>
            </div>
            <div class="compare-col">
                <h4>🔮 预测 Top 1</h4>
                <div class="numbers-display">
                    <div class="red-balls">${result.predicted_red.map(n => `<div class="ball red-ball" style="width:35px;height:35px; ${result.actual_red.includes(n) ? 'border:2px solid gold;box-shadow:0 0 8px gold;' : ''}">${String(n).padStart(2,'0')}</div>`).join('')}</div>
                    <span class="separator">+</span>
                    <div class="blue-balls">${result.predicted_blue.map(n => `<div class="ball blue-ball" style="width:35px;height:35px; ${result.actual_blue.includes(n) ? 'border:2px solid gold;box-shadow:0 0 8px gold;' : ''}">${String(n).padStart(2,'0')}</div>`).join('')}</div>
                </div>
            </div>
        </div>
    `;
    container.insertBefore(item, container.firstChild); // 最新的显示在最上面
}

// 导出组合
async function exportCombinations() {
    // 防重复点击
    if (isExporting) {
        return;
    }
    
    // 获取杀号输入
    const killRedInput = document.getElementById('exportKillRed').value.trim();
    const killBlueInput = document.getElementById('exportKillBlue').value.trim();
    const sumMinInput = document.getElementById('exportSumMin').value.trim();
    const sumMaxInput = document.getElementById('exportSumMax').value.trim();
    const oddEvenRatio = document.getElementById('exportOddEvenRatio').value.trim();
    
    // 解析杀号
    const killRed = killRedInput ? killRedInput.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n) && n >= 1 && n <= 35) : [];
    const killBlue = killBlueInput ? killBlueInput.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n) && n >= 1 && n <= 12) : [];
    
    // 解析和值范围
    let sumMin = null;
    let sumMax = null;
    if (sumMinInput && sumMaxInput) {
        sumMin = parseInt(sumMinInput);
        sumMax = parseInt(sumMaxInput);
        if (sumMin < 15 || sumMax > 175 || sumMin > sumMax) {
            alert('和值范围无效！最小值不能小于15，最大值不能大于175，且最小值不能大于最大值');
            return;
        }
    }
    
    // 确认提示
    let confirmMsg = '导出过程需要较长时间（可耉10-30分钟）';
    if (killRed.length > 0 || killBlue.length > 0 || sumMin !== null || oddEvenRatio) {
        confirmMsg += '\n\n过滤条件：';
        if (killRed.length > 0) {
            confirmMsg += `\n  红球：${killRed.map(n => String(n).padStart(2, '0')).join(', ')}`;
        }
        if (killBlue.length > 0) {
            confirmMsg += `\n  蓝球：${killBlue.map(n => String(n).padStart(2, '0')).join(', ')}`;
        }
        if (sumMin !== null && sumMax !== null) {
            confirmMsg += `\n  和值范围：${sumMin} - ${sumMax}`;
        }
        if (oddEvenRatio) {
            confirmMsg += `\n  奇偶比：${oddEvenRatio}`;
        }
        confirmMsg += '\n\n将排除不符合条件的所有组合';
    }
    confirmMsg += '\n\n确认继续？';
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    // 设置状态和禁用按钮
    isExporting = true;
    const exportBtn = document.querySelector('.export-section .btn-warning');
    const originalText = exportBtn.textContent;
    exportBtn.disabled = true;
    exportBtn.textContent = '导出中...';
    
    // 显示加载状态
    document.getElementById('exportLoading').style.display = 'block';
    document.getElementById('exportResults').innerHTML = '';
    
    // 生成并记录任务ID
    const taskId = 'export_' + Date.now();
    activeTaskIds['predict'] = taskId; // 导出也使用预测区的停止按钮
    toggleStopButton('predict', true);
    
    try {
        const response = await fetch(`${API_BASE}/api/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_id: taskId,
                kill_red: killRed,
                kill_blue: killBlue,
                sum_min: sumMin,
                sum_max: sumMax,
                odd_even_ratio: oddEvenRatio
            })
        });
        
        const data = await response.json();
        
        const resultsDiv = document.getElementById('exportResults');
        
        if (data.success) {
            let killInfo = '';
            if (data.kill_red && data.kill_red.length > 0) {
                killInfo += `<p style="font-size: 14px; color: #666;"><strong>杀红球：</strong>${data.kill_red.map(n => String(n).padStart(2, '0')).join(', ')}</p>`;
            }
            if (data.kill_blue && data.kill_blue.length > 0) {
                killInfo += `<p style="font-size: 14px; color: #666;"><strong>杀蓝球：</strong>${data.kill_blue.map(n => String(n).padStart(2, '0')).join(', ')}</p>`;
            }
            if (data.sum_range) {
                killInfo += `<p style="font-size: 14px; color: #666;"><strong>和值范围：</strong>${data.sum_range[0]} - ${data.sum_range[1]}</p>`;
            }
            if (data.odd_even_ratio) {
                killInfo += `<p style="font-size: 14px; color: #666;"><strong>奇偶比：</strong>${data.odd_even_ratio}</p>`;
            }
            
            resultsDiv.innerHTML = `
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 20px; margin-top: 20px;">
                    <h3 style="color: #155724; margin-top: 0;">✅ 导出成功！</h3>
                    <p style="font-size: 16px;"><strong>过滤后组合数：</strong>${data.filtered_count.toLocaleString()} 组</p>
                    ${killInfo}
                    <p style="font-size: 14px; color: #666;">${data.message}</p>
                    <p style="font-size: 14px; color: #666;">
                        <strong>导出目录：</strong>${data.export_dir}/<br>
                        请在项目根目录下查看导出的Excel文件
                    </p>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; margin-top: 20px;">
                    <h3 style="color: #721c24; margin-top: 0;">❌ 导出失败</h3>
                    <p style="color: #721c24;">${data.error}</p>
                    ${data.detail ? `<pre style="background: #fff; padding: 10px; overflow: auto; font-size: 12px;">${data.detail}</pre>` : ''}
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('exportResults').innerHTML = `
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; margin-top: 20px;">
                <h3 style="color: #721c24; margin-top: 0;">❌ 网络错误</h3>
                <p style="color: #721c24;">${error.message}</p>
            </div>
        `;
    } finally {
        document.getElementById('exportLoading').style.display = 'none';
        toggleStopButton('predict', false);
        activeTaskIds['predict'] = null;
        // 恢复按钮状态
        isExporting = false;
        exportBtn.disabled = false;
        exportBtn.textContent = originalText;
    }
}

// 查询组合
async function queryCombination() {
    const redInput = document.getElementById('queryRedNumbers').value.trim();
    const blueInput = document.getElementById('queryBlueNumbers').value.trim();
    
    if (!redInput || !blueInput) {
        alert('请输入完整的号码组合（前区5个号码和后区2个号码）');
        return;
    }
    
    // 解析输入
    const red_numbers = redInput.split(',').map(n => parseInt(n.trim()));
    const blue_numbers = blueInput.split(',').map(n => parseInt(n.trim()));
    
    // 验证号码
    if (red_numbers.length !== 5) {
        alert('请输入5个前区号码');
        return;
    }
    if (blue_numbers.length !== 2) {
        alert('请输入2个后区号码');
        return;
    }
    if (!red_numbers.every(n => n >= 1 && n <= 35)) {
        alert('前区号码必须在1-35之间');
        return;
    }
    if (!blue_numbers.every(n => n >= 1 && n <= 12)) {
        alert('后区号码必须在1-12之间');
        return;
    }
    
    // 获取过滤条件
    const killRedInput = document.getElementById('exportKillRed').value.trim();
    const killBlueInput = document.getElementById('exportKillBlue').value.trim();
    const sumMinInput = document.getElementById('exportSumMin').value.trim();
    const sumMaxInput = document.getElementById('exportSumMax').value.trim();
    const oddEvenRatio = document.getElementById('exportOddEvenRatio').value.trim();
    
    const kill_red = killRedInput ? killRedInput.split(',').map(n => parseInt(n.trim())).filter(n => n >= 1 && n <= 35) : [];
    const kill_blue = killBlueInput ? killBlueInput.split(',').map(n => parseInt(n.trim())).filter(n => n >= 1 && n <= 12) : [];
    
    let sum_min = null;
    let sum_max = null;
    if (sumMinInput && sumMaxInput) {
        sum_min = parseInt(sumMinInput);
        sum_max = parseInt(sumMaxInput);
    }
    
    document.getElementById('queryLoading').style.display = 'block';
    document.getElementById('queryResults').innerHTML = '';
    
    // 生成并记录任务ID
    const taskId = 'query_' + Date.now();
    activeTaskIds['predict'] = taskId; // 查询也使用预测区的停止按钮
    toggleStopButton('predict', true);
    
    try {
        const response = await fetch(`${API_BASE}/api/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_id: taskId,
                red_numbers: red_numbers,
                blue_numbers: blue_numbers,
                kill_red: kill_red,
                kill_blue: kill_blue,
                sum_min: sum_min,
                sum_max: sum_max,
                odd_even_ratio: oddEvenRatio
            })
        });
        
        const data = await response.json();
        const resultsDiv = document.getElementById('queryResults');
        
        if (data.success) {
            const statusColor = data.is_in_filtered ? '#d4edda' : '#f8d7da';
            const statusBorder = data.is_in_filtered ? '#c3e6cb' : '#f5c6cb';
            const statusTextColor = data.is_in_filtered ? '#155724' : '#721c24';
            const statusIcon = data.is_in_filtered ? '✅' : '❌';
            
            resultsDiv.innerHTML = `
                <div style="background: ${statusColor}; border: 1px solid ${statusBorder}; border-radius: 5px; padding: 20px; margin-top: 20px;">
                    <h3 style="color: ${statusTextColor}; margin-top: 0;">${statusIcon} ${data.message}</h3>
                    <p style="color: ${statusTextColor}; font-size: 18px; font-weight: bold;">
                        组合: ${data.combination}
                    </p>
                    <p style="color: ${statusTextColor};">
                        <strong>前区和值：</strong>${data.red_sum}<br>
                        <strong>奇偶比：</strong>${data.odd_even_ratio}<br>
                        <strong>过滤后总组合数：</strong>${data.total_filtered.toLocaleString()}
                    </p>
                </div>
            `;
        } else {
            resultsDiv.innerHTML = `
                <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; margin-top: 20px;">
                    <h3 style="color: #721c24; margin-top: 0;">❌ 查询失败</h3>
                    <p style="color: #721c24;">${data.error}</p>
                </div>
            `;
        }
    } catch (error) {
        document.getElementById('queryResults').innerHTML = `
            <div style="background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 5px; padding: 20px; margin-top: 20px;">
                <h3 style="color: #721c24; margin-top: 0;">❌ 网络错误</h3>
                <p style="color: #721c24;">${error.message}</p>
            </div>
        `;
    } finally {
        document.getElementById('queryLoading').style.display = 'none';
        toggleStopButton('predict', false);
        activeTaskIds['predict'] = null;
    }
}

// 页面加载时自动加载历史数据
window.addEventListener('load', () => {
    loadHistory();
});

// 回车键触发预测
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('exportPeriod').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            predict();
        }
    });
});

/**
 * 通用流式获取函数
 */
async function streamFetch(url, body, onData, onDone, onError) {
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop();

            for (const line of lines) {
                const trimmedLine = line.trim();
                if (trimmedLine.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(trimmedLine.substring(6));
                        if (data.type === 'error') {
                            throw new Error(data.error);
                        }
                        if (data.type === 'done') {
                            if (onDone) onDone(data);
                            return;
                        }
                        onData(data);
                    } catch (e) {
                        console.error('解析流数据失败:', e, line);
                    }
                }
            }
        }
        if (onDone) onDone();
    } catch (error) {
        if (onError) onError(error);
        else console.error('Stream fetch error:', error);
    }
}
