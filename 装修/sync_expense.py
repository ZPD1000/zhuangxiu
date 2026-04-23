#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装修记账数据同步工具
- 读取 CSV 数据
- 生成 HTML 网页
- 提交到 Git
"""

import csv
import os
from datetime import datetime
from pathlib import Path

# 路径配置
WORKSPACE = Path("/home/admin/.openclaw/workspace")
CSV_PATH = WORKSPACE / "装修" / "装修支出记录表.csv"
HTML_TEMPLATE = WORKSPACE / "装修" / "expense_template.html"
HTML_OUTPUT = Path("/home/admin/uploads/decoration-expense.html")
GIT_REPO = WORKSPACE

# 预算配置（万元）
BUDGET_CONFIG = {
    "土建改造": {"percent": 18, "budget": 180000, "note": "下沉客厅、打墙、电梯井"},
    "水电改造": {"percent": 15, "budget": 150000, "note": "全屋水电、燃气管道"},
    "电梯安装": {"percent": 10, "budget": 100000, "note": "电梯 + 安装 + 井道"},
    "泥木工": {"percent": 12, "budget": 120000, "note": "地面、墙面、吊顶"},
    "门窗系统": {"percent": 10, "budget": 100000, "note": "断桥铝、系统窗、入户门"},
    "真火壁炉": {"percent": 6, "budget": 60000, "note": "壁炉 + 烟道 + 燃气系统"},
    "全屋定制": {"percent": 10, "budget": 100000, "note": "柜子、楼梯、影音室"},
    "软装家具": {"percent": 8, "budget": 80000, "note": "沙发、床、窗帘"},
    "花园景观": {"percent": 5, "budget": 50000, "note": "庭院、户外家具"},
    "设计费": {"percent": 0, "budget": 33000, "note": "装修设计"},
    "装修手续": {"percent": 0, "budget": 10000, "note": "押金、清运费等"},
    "材料费": {"percent": 0, "budget": 5000, "note": "辅材、工具"},
    "电气工程": {"percent": 0, "budget": 5000, "note": "电缆、开关"},
    "工具类": {"percent": 0, "budget": 2000, "note": "施工工具"},
}

TOTAL_BUDGET = 1000000


def read_csv_data():
    """读取 CSV 数据"""
    records = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        # 处理中文逗号
        content = f.read().replace('，', ',')
        lines = content.strip().split('\n')
        headers = [h.strip() for h in lines[0].split(',')]
        
        for line in lines[1:]:
            if not line.strip():
                continue
            values = [v.strip() for v in line.split(',')]
            if len(values) >= len(headers):
                row = dict(zip(headers, values))
                records.append(row)
    
    return records


def calculate_stats(records):
    """计算统计数据"""
    stats = {
        "total_paid": 0,
        "total_pending": 0,
        "category_stats": {},
        "records": records,
    }
    
    for r in records:
        try:
            paid = float(r.get('已付 (元)', 0) or 0)
            total = float(r.get('总价 (元)', 0) or 0)
            category = r.get('类别', '其他')
            
            stats["total_paid"] += paid
            stats["total_pending"] += (total - paid)
            
            if category not in stats["category_stats"]:
                stats["category_stats"][category] = {"paid": 0, "pending": 0}
            stats["category_stats"][category]["paid"] += paid
            stats["category_stats"][category]["pending"] += (total - paid)
        except (ValueError, TypeError) as e:
            print(f"⚠️ 解析错误：{r} - {e}")
    
    return stats


def generate_html(stats):
    """生成 HTML 网页"""
    records = stats["records"]
    total_paid = stats["total_paid"]
    total_pending = stats["total_pending"]
    category_stats = stats["category_stats"]
    
    # 生成支出记录表格行
    records_html = ""
    for r in records:
        status_class = "paid" if "已付" in r.get('付款状态', '') else "partial"
        if "未付" in r.get('付款状态', ''):
            status_class = "unpaid"
        
        records_html += f"""
                        <tr>
                            <td>{r.get('日期', '')}</td>
                            <td><strong>{r.get('项目名称', '')}</strong></td>
                            <td>{r.get('类别', '')}</td>
                            <td>{r.get('支出类型', '')}</td>
                            <td><strong>{r.get('总价 (元)', '0')}</strong></td>
                            <td><strong>{r.get('已付 (元)', '0')}</strong></td>
                            <td>{r.get('供应商/商家', '待定')}</td>
                            <td>{r.get('备注', '')}</td>
                            <td><span class="status {status_class}">{r.get('付款状态', '')}</span></td>
                        </tr>"""
    
    # 生成预算分配表格行
    budget_html = ""
    for cat, config in BUDGET_CONFIG.items():
        paid = category_stats.get(cat, {}).get("paid", 0)
        pending = config["budget"] - paid
        budget_html += f"""
                        <tr>
                            <td>{cat}</td>
                            <td>{config['percent']}%</td>
                            <td>{config['budget']:,}</td>
                            <td>{paid:,.0f}</td>
                            <td>{pending:,.0f}</td>
                            <td>{config['note']}</td>
                        </tr>"""
    
    # 合计行
    budget_html += f"""
                    <tr style="background: #667eea; color: white; font-weight: bold;">
                        <td>合计</td>
                        <td>100%</td>
                        <td>{TOTAL_BUDGET:,}</td>
                        <td>{total_paid:,.0f}</td>
                        <td>{TOTAL_BUDGET - total_paid:,.0f}</td>
                        <td>总预算含设计费</td>
                    </tr>"""
    
    # 支付进度
    progress = (total_paid / TOTAL_BUDGET * 100) if TOTAL_BUDGET > 0 else 0
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏠 装修支出记录清单</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
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
        .header h1 {{ font-size: 32px; margin-bottom: 10px; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 40px; }}
        .section h2 {{
            color: #333;
            font-size: 24px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
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
        td {{ padding: 12px 15px; border-bottom: 1px solid #e0e0e0; }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        tr:hover {{ background: #e9ecef; }}
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status.paid {{ background: #e8f5e9; color: #2e7d32; }}
        .status.partial {{ background: #fff3e0; color: #f57c00; }}
        .status.unpaid {{ background: #ffebee; color: #c62828; }}
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
        .summary-item {{ text-align: center; }}
        .summary-item h4 {{ font-size: 14px; opacity: 0.9; margin-bottom: 8px; }}
        .summary-item p {{ font-size: 28px; font-weight: 700; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #999;
            font-size: 13px;
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
        }}
        .chart-container h3 {{
            color: #333;
            font-size: 16px;
            margin-bottom: 15px;
            text-align: center;
        }}
        .chart-wrapper {{ position: relative; height: 300px; }}
        @media (max-width: 1024px) {{
            .charts-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 装修支出记录清单</h1>
            <p>融创福州府 C29-107 · 4 层叠拼 +300㎡花园</p>
        </div>

        <div class="content">
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
                        {budget_html}
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
                        {records_html}
                    </tbody>
                </table>
            </div>

            <div class="summary">
                <div class="summary-grid">
                    <div class="summary-item">
                        <h4>总预算</h4>
                        <p>¥{TOTAL_BUDGET:,}</p>
                    </div>
                    <div class="summary-item">
                        <h4>已付金额</h4>
                        <p>¥{total_paid:,.0f}</p>
                    </div>
                    <div class="summary-item">
                        <h4>待付金额</h4>
                        <p>¥{total_pending:,.0f}</p>
                    </div>
                    <div class="summary-item">
                        <h4>支付进度</h4>
                        <p>{progress:.1f}%</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="footer">
            <p>最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            <p>数据源：装修支出记录表.csv</p>
        </div>
    </div>

    <script>
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: {{
                labels: ['土建', '水电', '电梯', '泥木', '门窗', '壁炉', '定制', '软装', '花园', '设计'],
                datasets: [
                    {{
                        label: '预算',
                        data: [180000, 150000, 100000, 120000, 100000, 60000, 100000, 80000, 50000, 33000],
                        backgroundColor: 'rgba(102, 126, 234, 0.7)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 2
                    }},
                    {{
                        label: '已付',
                        data: [
                            {category_stats.get('土建工程', {}).get('paid', 0)},
                            {category_stats.get('电气工程', {}).get('paid', 0)},
                            {category_stats.get('电梯安装', {}).get('paid', 0)},
                            0,
                            {category_stats.get('装修手续', {}).get('paid', 0) + category_stats.get('门窗系统', {}).get('paid', 0)},
                            0,
                            0,
                            0,
                            {category_stats.get('工具类', {}).get('paid', 0) + category_stats.get('材料费', {}).get('paid', 0)},
                            {category_stats.get('设计费', {}).get('paid', 0)}
                        ],
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
                    legend: {{ position: 'top' }},
                    tooltip: {{
                        callbacks: {{
                            label: (ctx) => `¥${{ctx.parsed.y.toLocaleString()}}`
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{ callback: (v) => `¥${{(v/10000).toFixed(1)}}万` }}
                    }}
                }}
            }}
        }});

        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {{
            type: 'doughnut',
            data: {{
                labels: ['土建 18%', '水电 15%', '电梯 10%', '泥木 12%', '门窗 10%', '壁炉 6%', '定制 10%', '软装 8%', '花园 5%'],
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
                plugins: {{ legend: {{ position: 'right' }} }}
            }}
        }});
    </script>
</body>
</html>"""
    
    return html


def git_commit_and_push():
    """提交并推送到 GitHub"""
    import subprocess
    
    os.chdir(GIT_REPO)
    
    try:
        # 添加文件
        subprocess.run(["git", "add", "装修/装修支出记录表.csv", "装修/装修进度跟踪表.md"], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 检查是否有变更
        result = subprocess.run(["git", "diff", "--cached", "--quiet"], 
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            print("✅ 没有变更，跳过提交")
            return
        
        # 提交
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        subprocess.run(["git", "commit", "-m", f"📝 更新装修记账数据 - {timestamp}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 推送
        result = subprocess.run(["git", "push"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print(f"⚠️ 推送失败，请检查 Git 配置")
        else:
            print("✅ 已推送到 GitHub")
    except Exception as e:
        print(f"⚠️ Git 操作失败：{e}")
        print("   请手动运行：cd /home/admin/.openclaw/workspace && git add . && git commit -m 'update' && git push")


def main():
    print("🔄 装修记账数据同步工具")
    print("=" * 50)
    
    # 读取数据
    print("📖 读取 CSV 数据...")
    records = read_csv_data()
    print(f"   找到 {len(records)} 条记录")
    
    # 计算统计
    print("📊 计算统计数据...")
    stats = calculate_stats(records)
    print(f"   已付：¥{stats['total_paid']:,.0f}")
    print(f"   待付：¥{stats['total_pending']:,.0f}")
    
    # 生成 HTML
    print("🎨 生成 HTML 网页...")
    html = generate_html(stats)
    
    # 保存 HTML
    HTML_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"   已保存：{HTML_OUTPUT}")
    
    # Git 提交
    print("🚀 同步到 GitHub...")
    git_commit_and_push()
    
    print("=" * 50)
    print("✅ 同步完成！")
    print(f"🌐 访问地址：http://39.102.49.68:8899/decoration-expense.html")


if __name__ == "__main__":
    main()
