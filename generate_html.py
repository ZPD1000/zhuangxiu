#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装修支出记录 HTML 生成器
根据 CSV 数据自动生成统计网页
"""

from datetime import datetime
from collections import defaultdict

# 读取 CSV 数据（混用中英文逗号）
def read_csv(filepath):
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 跳过表头
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        # 中文逗号（\uff0c）替换为英文逗号
        line = line.replace('\uff0c', ',')
        # 分割
        parts = line.split(',')
        if len(parts) >= 11:
            record = {
                '日期': parts[0],
                '项目名称': parts[1],
                '类别': parts[2],
                '支出类型': parts[3],
                '单价': float(parts[4]) if parts[4] else 0,
                '数量': int(parts[5]) if parts[5] else 1,
                '总价': float(parts[6]) if parts[6] else 0,
                '已付': float(parts[7]) if parts[7] else 0,
                '供应商': parts[8] if len(parts) > 8 else '',
                '备注': parts[9] if len(parts) > 9 else '',
                '付款状态': parts[10] if len(parts) > 10 else '',
            }
            records.append(record)
    return records

# 计算统计数据
def calc_stats(records):
    total_budget = 1000000  # 总预算 100 万
    
    # 按类别汇总
    category_stats = defaultdict(lambda: {'budget': 0, 'actual': 0, 'paid': 0})
    
    # 预算分配（固定）
    budget_allocation = {
        '土建改造': 180000,
        '水电改造': 150000,
        '电梯安装': 100000,
        '泥木工': 120000,
        '门窗系统': 100000,
        '真火壁炉': 60000,
        '全屋定制': 100000,
        '软装家具': 80000,
        '花园景观': 50000,
        '设计费': 33000,
    }
    
    total_actual = 0
    total_paid = 0
    
    for record in records:
        category = record['类别']
        actual = record['总价']
        paid = record['已付']
        
        total_actual += actual
        total_paid += paid
        
        category_stats[category]['actual'] += actual
        category_stats[category]['paid'] += paid
    
    # 设置预算
    for cat, budget in budget_allocation.items():
        category_stats[cat]['budget'] = budget
    
    return {
        'total_budget': total_budget,
        'total_actual': total_actual,
        'total_paid': total_paid,
        'total_pending': total_actual - total_paid,
        'paid_percentage': (total_paid / total_actual * 100) if total_actual > 0 else 0,
        'category_stats': dict(category_stats),
        'budget_allocation': budget_allocation,
    }

# 生成 HTML
def generate_html(records, stats, output_path):
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 预算分配表行
    budget_rows = []
    budget_order = [
        ('土建改造', '下沉客厅、打墙、电梯井'),
        ('水电改造', '全屋水电、燃气管道'),
        ('电梯安装', '电梯 + 安装 + 井道'),
        ('泥木工', '地面、墙面、吊顶'),
        ('门窗系统', '断桥铝、系统窗、入户门'),
        ('真火壁炉', '壁炉 + 烟道 + 燃气系统'),
        ('全屋定制', '柜子、楼梯、影音室'),
        ('软装家具', '沙发、床、窗帘'),
        ('花园景观', '庭院、户外家具'),
        ('设计费', '装修设计'),
    ]
    
    for cat, note in budget_order:
        budget = stats['budget_allocation'].get(cat, 0)
        paid = stats['category_stats'].get(cat, {}).get('paid', 0)
        # 土建改造需要合并土建工程的支付
        if cat == '土建改造':
            paid = stats['category_stats'].get('土建工程', {}).get('paid', 0)
        remaining = budget - paid
        percentage = (budget / stats['total_budget'] * 100) if budget > 0 else 0
        
        budget_rows.append(f'''
                        <tr>
                            <td>{cat}</td>
                            <td>{percentage:.0f}%</td>
                            <td>{budget:,}</td>
                            <td>{paid:,.0f}</td>
                            <td>{remaining:,.0f}</td>
                            <td>{note}</td>
                        </tr>''')
    
    # 合计行
    total_budget_pct = sum(stats['budget_allocation'].values()) / stats['total_budget'] * 100
    budget_rows.append(f'''
                        <tr style="background: #667eea; color: white; font-weight: bold;">
                            <td>合计</td>
                            <td>{total_budget_pct:.0f}%</td>
                            <td>{stats['total_budget']:,}</td>
                            <td>{stats['total_paid']:,.0f}</td>
                            <td>{stats['total_budget'] - stats['total_paid']:,.0f}</td>
                            <td>总预算含设计费</td>
                        </tr>''')
    
    # 支出记录行
    expense_rows = []
    for record in records:
        status_class = 'unpaid'
        status_text = '未付'
        if '已付' in record['付款状态']:
            status_class = 'paid'
            status_text = '已付'
        elif '部分' in record['付款状态'] or '预付款' in record['支出类型']:
            status_class = 'partial'
            status_text = '部分支付'
        
        expense_rows.append(f'''
                        <tr>
                            <td>{record['日期']}</td>
                            <td>{record['项目名称']}</td>
                            <td>{record['类别']}</td>
                            <td>{record['支出类型']}</td>
                            <td><strong>{record['总价']:,.0f}</strong></td>
                            <td><strong>{record['已付']:,.0f}</strong></td>
                            <td>{record['供应商']}</td>
                            <td>{record['备注']}</td>
                            <td><span class="status {status_class}">{status_text}</span></td>
                        </tr>''')
    
    # 本月支出行（3 月）
    march_rows = []
    for record in records:
        if record['日期'].startswith('2026-03'):
            paid = record['已付']
            march_rows.append(f'''
                        <tr>
                            <td>{record['日期']}</td>
                            <td>{record['项目名称']}</td>
                            <td>{record['总价']:,.0f}</td>
                            <td><strong>{paid:,.0f}</strong></td>
                            <td>-</td>
                            <td>{record['支出类型']}</td>
                        </tr>''')
    
    march_rows.append(f'''
                        <tr style="background: #667eea; color: white; font-weight: bold;">
                            <td colspan="2">本月合计</td>
                            <td>{stats['total_actual']:,.0f}</td>
                            <td><strong>{stats['total_paid']:,.0f}</strong></td>
                            <td>-</td>
                            <td>已付</td>
                        </tr>''')
    
    # 图表数据
    bar_labels = ['土建', '水电', '电梯', '泥木', '门窗', '壁炉', '定制', '软装', '花园', '设计']
    bar_budget = [
        stats['budget_allocation'].get('土建改造', 0),
        stats['budget_allocation'].get('水电改造', 0),
        stats['budget_allocation'].get('电梯安装', 0),
        stats['budget_allocation'].get('泥木工', 0),
        stats['budget_allocation'].get('门窗系统', 0),
        stats['budget_allocation'].get('真火壁炉', 0),
        stats['budget_allocation'].get('全屋定制', 0),
        stats['budget_allocation'].get('软装家具', 0),
        stats['budget_allocation'].get('花园景观', 0),
        stats['budget_allocation'].get('设计费', 0),
    ]
    
    # 土建已付 = 土建工程已付
    civil_paid = stats['category_stats'].get('土建工程', {}).get('paid', 0)
    bar_paid = [
        civil_paid,
        stats['category_stats'].get('水电改造', {}).get('paid', 0),
        stats['category_stats'].get('电梯安装', {}).get('paid', 0),
        stats['category_stats'].get('泥木工', {}).get('paid', 0),
        stats['category_stats'].get('门窗系统', {}).get('paid', 0),
        stats['category_stats'].get('真火壁炉', {}).get('paid', 0),
        stats['category_stats'].get('全屋定制', {}).get('paid', 0),
        stats['category_stats'].get('软装家具', {}).get('paid', 0),
        stats['category_stats'].get('花园景观', {}).get('paid', 0),
        stats['category_stats'].get('设计费', {}).get('paid', 0),
    ]
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="Content-Disposition" content="inline">
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 装修支出记录清单</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}

        .content {{
            padding: 30px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            color: #333;
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}

        .info-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .info-card h3 {{
            color: #667eea;
            font-size: 14px;
            margin-bottom: 8px;
        }}

        .info-card p {{
            color: #333;
            font-size: 18px;
            font-weight: 500;
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}

        .chart-container {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        .chart-container h3 {{
            color: #333;
            font-size: 16px;
            margin-bottom: 15px;
            text-align: center;
        }}

        .chart-wrapper {{
            position: relative;
            height: 300px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}

        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}

        tr:nth-child(even) {{
            background: #f8f9fa;
        }}

        tr:hover {{
            background: #e9ecef;
        }}

        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}

        .status.unpaid {{
            background: #ffebee;
            color: #c62828;
        }}

        .status.partial {{
            background: #fff3e0;
            color: #f57c00;
        }}

        .status.paid {{
            background: #e8f5e9;
            color: #2e7d32;
        }}

        .summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin-top: 20px;
        }}

        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
        }}

        .summary-item {{
            text-align: center;
        }}

        .summary-item h4 {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 8px;
        }}

        .summary-item p {{
            font-size: 28px;
            font-weight: 700;
        }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 13px;
        }}

        @media (max-width: 1024px) {{
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 768px) {{
            .content {{
                padding: 15px;
            }}

            table {{
                font-size: 12px;
            }}

            th, td {{
                padding: 8px 10px;
            }}

            .chart-wrapper {{
                height: 250px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 装修支出记录清单</h1>
            <p>融创福州府 C29-107 · 4 层叠拼 + 300㎡花园</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>📋 基本信息</h2>
                <div class="info-grid">
                    <div class="info-card">
                        <h3>总面积</h3>
                        <p>约 300㎡ (室内) + 300㎡ (花园)</p>
                    </div>
                    <div class="info-card">
                        <h3>总预算</h3>
                        <p>100 万元 (含设计费)</p>
                    </div>
                    <div class="info-card">
                        <h3>装修风格</h3>
                        <p>自然风 / 中古风</p>
                    </div>
                    <div class="info-card">
                        <h3>开工时间</h3>
                        <p>2026 年 3 月</p>
                    </div>
                    <div class="info-card">
                        <h3>预计工期</h3>
                        <p>12 个月</p>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>📊 数据可视化</h2>
                <div class="charts-grid">
                    <div class="chart-container">
                        <h3>📈 预算 vs 实际支出对比</h3>
                        <div class="chart-wrapper">
                            <canvas id="barChart"></canvas>
                        </div>
                    </div>
                    <div class="chart-container">
                        <h3>🥧 预算分配饼图</h3>
                        <div class="chart-wrapper">
                            <canvas id="pieChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>💰 预算分配</h2>
                <table>
                    <thead>
                        <tr>
                            <th>项目类别</th>
                            <th>预算占比</th>
                            <th>预算金额 (元)</th>
                            <th>实际支出 (元)</th>
                            <th>结余 (元)</th>
                            <th>备注</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(budget_rows)}
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>📝 支出记录</h2>
                <table>
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>项目名称</th>
                            <th>类别</th>
                            <th>支出类型</th>
                            <th>总价 (元)</th>
                            <th>已付 (元)</th>
                            <th>供应商/商家</th>
                            <th>备注</th>
                            <th>付款状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(expense_rows)}
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>📅 本月支出记录（2026 年 3 月）</h2>
                <table>
                    <thead>
                        <tr>
                            <th>日期</th>
                            <th>项目</th>
                            <th>预计总价 (元)</th>
                            <th>实付金额 (元)</th>
                            <th>付款人</th>
                            <th>状态</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(march_rows)}
                    </tbody>
                </table>
            </div>

            <div class="summary">
                <div class="summary-grid">
                    <div class="summary-item">
                        <h4>总预算</h4>
                        <p>¥{stats['total_budget']:,}</p>
                    </div>
                    <div class="summary-item">
                        <h4>已付金额</h4>
                        <p>¥{stats['total_paid']:,.0f}</p>
                    </div>
                    <div class="summary-item">
                        <h4>待付金额</h4>
                        <p>¥{stats['total_pending']:,.0f}</p>
                    </div>
                    <div class="summary-item">
                        <h4>支付进度</h4>
                        <p>{stats['paid_percentage']:.1f}%</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>最后更新：{today}</p>
            <p>建议每笔支出后立即更新，每周汇总一次</p>
        </div>
    </div>

    <script>
        // 柱状图：预算 vs 实际支出
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: {bar_labels},
                datasets: [
                    {{
                        label: '预算',
                        data: {bar_budget},
                        backgroundColor: 'rgba(102, 126, 234, 0.7)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 2
                    }},
                    {{
                        label: '已付',
                        data: {bar_paid},
                        backgroundColor: 'rgba(118, 75, 162, 0.7)',
                        borderColor: 'rgba(118, 75, 162, 1)',
                        borderWidth: 2
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                let label = context.dataset.label || '';
                                if (label) {{
                                    label += ': ';
                                }}
                                if (context.parsed.y !== null) {{
                                    label += new Intl.NumberFormat('zh-CN', {{ style: 'currency', currency: 'CNY' }}).format(context.parsed.y);
                                }}
                                return label;
                            }}
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return '¥' + (value / 10000) + '万';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // 饼图：预算分配
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['土建改造 18%', '水电改造 15%', '电梯安装 10%', '泥木工 12%', '门窗系统 10%', '真火壁炉 6%', '全屋定制 10%', '软装家具 8%', '花园景观 5%'],
                datasets: [{{
                    data: [180000, 150000, 100000, 120000, 100000, 60000, 100000, 80000, 50000],
                    backgroundColor: [
                        'rgba(102, 126, 234, 0.8)',
                        'rgba(118, 75, 162, 0.8)',
                        'rgba(245, 101, 101, 0.8)',
                        'rgba(72, 187, 120, 0.8)',
                        'rgba(66, 153, 225, 0.8)',
                        'rgba(255, 159, 64, 0.8)',
                        'rgba(153, 102, 255, 0.8)',
                        'rgba(255, 99, 132, 0.8)',
                        'rgba(75, 192, 192, 0.8)'
                    ],
                    borderColor: '#fff',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                let label = context.label || '';
                                if (label) {{
                                    return label;
                                }}
                                let value = context.parsed;
                                return new Intl.NumberFormat('zh-CN', {{ style: 'currency', currency: 'CNY' }}).format(value);
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML 已生成：{output_path}")
    print(f"📊 统计数据:")
    print(f"   总预算：¥{stats['total_budget']:,}")
    print(f"   已付金额：¥{stats['total_paid']:,.0f}")
    print(f"   待付金额：¥{stats['total_pending']:,.0f}")
    print(f"   支付进度：{stats['paid_percentage']:.1f}%")

if __name__ == '__main__':
    csv_path = '/home/admin/uploads/装修/装修支出记录表.csv'
    html_path = '/home/admin/uploads/装修/装修支出记录.html'
    
    records = read_csv(csv_path)
    print(f"读取到 {len(records)} 条记录")
    for r in records:
        print(f"  - {r['日期']} {r['项目名称']}: 总价{r['总价']} 已付{r['已付']}")
    
    stats = calc_stats(records)
    generate_html(records, stats, html_path)
