#!/usr/bin/env python3
"""Create a self-contained Korean research report from results.json.

Requires reportlab for standard vector charts. No network or source writes.
"""
import html
import json
import re
from pathlib import Path

from reportlab.graphics.shapes import Drawing, String, Rect
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderSVG
from reportlab.lib.colors import HexColor

HERE=Path(__file__).resolve().parent
X=json.loads((HERE/'results.json').read_text())
LABELS={'strata':'Strata','physlib':'PhysLib','cslib':'CSLib','arklib':'ArkLib','leanpool':'LeanPool'}


def f(v,d=1):
    return '—' if v is None else f'{v:,.{d}f}'


def esc(s):
    return html.escape(str(s))


def table(headers,rows):
    return '<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+esc(h)+'</th>' for h in headers)+\
        '</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+str(v)+'</td>' for v in r)+'</tr>' for r in rows)+\
        '</tbody></table></div>'


def chart(name,title,categories,data,legend,maximum):
    d=Drawing(700,310)
    d.add(String(32,289,title,fontName='Helvetica-Bold',fontSize=14,fillColor=HexColor('#172d39')))
    bc=VerticalBarChart();bc.x=55;bc.y=58;bc.height=205;bc.width=610
    bc.data=data;bc.categoryAxis.categoryNames=categories
    bc.valueAxis.valueMin=0;bc.valueAxis.valueMax=maximum
    bc.valueAxis.valueStep=5 if maximum==25 else 20
    bc.valueAxis.visibleGrid=True;bc.valueAxis.gridStrokeColor=HexColor('#e4e9eb')
    bc.categoryAxis.labels.fontName='Helvetica';bc.categoryAxis.labels.fontSize=10
    bc.valueAxis.labels.fontSize=9
    colors=['#186a6b','#d29241']
    for i,c in enumerate(colors):bc.bars[i].fillColor=HexColor(c);bc.bars[i].strokeColor=None
    d.add(bc)
    for i,label in enumerate(legend):
        d.add(Rect(55+i*260,15,12,12,fillColor=HexColor(colors[i]),strokeColor=None))
        d.add(String(74+i*260,16,label,fontSize=10,fillColor=HexColor('#172d39')))
    renderSVG.drawToFile(d,str(HERE/name))
    svg=(HERE/name).read_text()
    svg=svg[svg.index('<svg'):].replace('<title>...</title>',f'<title>{esc(title)}</title>')
    svg=svg.replace('<desc>...</desc>','<desc>Two-series comparison; exact values are in the adjacent report table.</desc>')
    prefix=Path(name).stem
    for ident in re.findall(r'id="([^"]+)"',svg):
        svg=svg.replace(f'id="{ident}"',f'id="{prefix}-{ident}"').replace(f'url(#{ident})',f'url(#{prefix}-{ident})')
    (HERE/name).write_text(svg)
    return svg


def section(id,title,content):
    return f'<section id="{id}"><h2>{title}</h2>{content}</section>'


def main():
    profiles=X['profiles']
    have_svg=chart('length-selection.svg','Proofs containing have: population vs long subset (%)',
        list(LABELS.values()),
        [[profiles[s]['tactics']['have'][key] for s in LABELS] for key in ['raw_percent','long_percent']],
        ['All eligible proofs','Proof length >= 200'],100)
    sections=[]

    rows=[]
    for s in LABELS:
        p=profiles[s];rows.append([LABELS[s],f(p['n'],0),f(p['unique_strings'],0),f(p['ge200'],0),f(p['length']['median'],0)])
    sections.append(section('scope','최종 50문제 후보군을 이해하기 위한 분석',
        '<p class="finding">분석 전제: 6개 출처에서 가져온 자료를 <strong>최종 50문제의 후보군</strong>으로 본다. '
        '후보들의 길이, 증명 방식, 출처와 하위 프로젝트의 특징을 파악하는 것이 목적이다.</p>'
        '<p>수집한 추출 선언 382,121개 중, 직접 <code>sorry/admit</code>가 없는 '
        '<code>by</code> 증명 323,207개를 연결했다. PutnamBench 원본에는 이 조건을 만족하는 증명이 없어 '
        '아래 완성 증명 통계에서 빠진다. 이는 PutnamBench가 최종 문제의 출처 후보에서 빠진다는 뜻이 아니다. '
        '완성된 Putnam warm-up 3개는 별도로 보관한다. 통계의 포함 조건과 최종 문제의 선정 조건을 구분한다.</p>'+
        table(['출처','분석 증명','고유 proof 문자열','200토큰 이상','길이 중앙값'],rows)+
        '<p>출처 간 풀이 표현 대조, 길이 분포 표준화, 파일 고정효과와 파일 재표집 400회, '
        'LeanPool 하위 프로젝트 비교, 길이를 맞춘 warm-up 비교 각 20,000회, '
        '긴 후보 48,519개의 proof·선언 원문 SHA-256 확인 결과를 정리했다.</p>'
        '<p class="note">아래 수치는 후보군의 구성에 관한 관찰이다. Lean 실행과 heartbeat 측정은 하지 않았다.</p>'))

    clones=X['long_clone_audit'];proof=clones['proof_sha256'];src=clones['src_sha256']
    cross=X['cross_source_overlap']['200'];nonzero=[r for r in cross if r['shared_unique_strings']]
    cross_all=next(r for r in X['cross_source_overlap']['0'] if r['a']=='physlib' and r['b']=='leanpool')
    sections.append(section('clones','1. 같은 풀이 표현이 서로 다른 후보에 쓰일 수 있다',
        '<p>서로 다른 명제도 <code>by rfl</code>, <code>by simp</code> 같은 동일한 코드로 증명할 수 있다. '
        '본문 문자열 일치는 <strong>풀이 표현의 재사용</strong>으로 읽으며, 후보를 제거하는 기준으로 쓰지 않는다.</p>'
        f'<p>긴 후보 <strong>48,519개</strong>에 서로 다른 proof 문자열 <strong>{f(proof["unique"],0)}개</strong>가 나타난다. '
        f'문자열별 첫 출현 이후의 반복 출현 수는 <strong>{f(proof["redundant_records"],0)}개 '
        f'({f(100*proof["redundant_records"]/proof["n"],2)}%)</strong>다. '
        f'명제와 증명이 함께 담긴 선언 원문 <code>src</code>가 그대로 반복되는 출현 수는 '
        f'<strong>{f(src["redundant_records"],0)}개</strong>다.</p>'+
        table(['일치 기준','서로 다른 문자열','첫 출현 이후 반복 수','반복 집단의 전체 행','출처 간 반복 집단','LeanPool 프로젝트 간 반복 집단'],
              [[label,f(v['unique'],0),f(v['redundant_records'],0),f(v['records_in_repeated_clusters'],0),
                v['cross_source_clusters'],v['cross_leanpool_group_clusters']]
               for label,v in [('proof 원문',proof),('선언 src 원문',src)]])+
        f'<p>PhysLib–LeanPool은 전체 범위에서 고유 proof 문자열 {cross_all["shared_unique_strings"]}개를 공유한다. '
        '200토큰 이상으로 제한하면 공유 문자열은 4개이며, 다른 출처 쌍에는 없다. 이 중 선언 원문까지 같은 집단은 3개다. '
        '공유되는 풀이 표현과 관련 후보의 위치를 살펴보는 단서다.</p>'+
        '<p class="note">“첫 출현 이후 반복 수”는 각 집단에서 첫 행을 뺀 수이고, “반복 집단의 전체 행”에는 첫 행도 포함한다. '
        '공백·주석을 포함한 바이트 동일성만 검사했다. 이름 바꾸기·포맷 차이·의미적 동등성은 잡지 못한다. '
        '같은 선언 src라도 파일 밖 namespace, import, 변수 문맥은 다를 수 있다. '
        '동일 문제인지는 명제·가정·문맥을 함께 살펴야 하며, 본문 일치만으로 다른 후보를 버리지 않는다.</p>'+
        '<details><summary>출처 간 공유 긴 증명의 위치</summary>'+
        table(['출처','정리','길이','파일'],[[LABELS[e['source']],esc(e['name']),e['length'],esc(e['file'])]
               for pair in nonzero for e in pair['examples']])+ '</details>'))

    h=X['leanpool_heterogeneity'];groups=[g for g in h['groups'] if g['n']>=100]
    extremes=sorted(groups,key=lambda g:g['length']['median'])
    macro_rows=[[f'<code>{t}</code>',f(h['micro_same_groups_tactic_percent'][t])+'%',
                 f(h['macro_tactic_percent'][t])+'%'] for t in ['simp','rw','apply','omega','norm_num']]
    sections.append(section('groups','2. LeanPool 후보들은 하위 프로젝트마다 성격이 다르다',
        f'<p>분석 대상이 있는 하위 경로 그룹은 <strong>{len(h["groups"])}개</strong>다. '
        f'크기 집중도를 역수로 표현한 유효 그룹 수 <code>1/Σp²</code>는 <strong>{f(h["effective_group_count"])}개</strong>다. '
        '이는 독립 표본 수가 아니라, 같은 크기의 그룹 몇 개가 현재 집중도와 같은지 나타내는 지표다.</p>'+
        f'<p>100개 이상 증명을 가진 {h["substantial_groups"]}개 그룹만 비교해도 길이 중앙값은 '
        f'<strong>{f(extremes[0]["length"]["median"])}–{f(extremes[-1]["length"]["median"])}</strong>토큰이다. '
        '이 그룹들의 길이 중앙값에 대한 10–90백분위는 '
        f'<strong>{f(h["median_across_substantial_groups"]["p10"])}–{f(h["median_across_substantial_groups"]["p90"])}토큰</strong>이다.</p>'+
        table(['tactic','행 수 가중 사용률','프로젝트 동등 평균'],macro_rows)+
        f'<p class="note">두 열 모두 같은 {h["substantial_groups"]}개 그룹, {f(h["substantial_group_records"],0)}개 증명 '
        f'(LeanPool 분석 대상의 {f(h["substantial_group_coverage_percent"],2)}%)을 사용한다. '
        '그룹은 <code>LeanPool/&lt;첫 하위 경로&gt;</code>로 정의하며 독립 연구 프로젝트임을 별도 검증하지는 않았다.</p>'+
        table(['그룹','증명 수','길이 중앙값','200토큰 이상'],[[esc(g['group']),f(g['n'],0),f(g['length']['median']),f(g['ge200_percent'])+'%']
              for g in extremes[:3]+extremes[-3:]])+
        '<p><strong>후보군을 읽는 관점:</strong> 큰 프로젝트의 특징이 전체 평균을 좌우할 수 있으므로, '
        'LeanPool 내부 그룹별 길이와 tactic 구성을 함께 살핀다. 후보가 많은 그룹에서 최종 문제가 더 많이 선정된다고 추정하지 않는다.</p>'))

    style=X['length_standardized']['unique_weighted']['sources']
    rows=[[LABELS[s]]+[f(style[s]['tactic_percent'][t])+'%' for t in ['grind','simp_all','induction','omega','fun_prop']] for s in LABELS]
    sections.append(section('style','3. 길이와 표현 반복을 고려해도 출처별 증명 방식이 다르다',
        '<p>고유 proof 문자열 하나에 총 가중치 1을 주고, 모든 출처의 길이 구간 비중을 같게 맞췄다. '
        '그 뒤에도 CSLib의 <code>grind</code>, Strata의 <code>simp_all</code>·귀납, ArkLib의 '
        '<code>omega</code>, PhysLib의 <code>fun_prop</code> 사용률 차이가 남는다.</p>'+
        table(['길이·표현 빈도 재가중 후','grind','simp_all','induction','omega','fun_prop'],rows)+
        '<p>사용률은 해당 구문이 한 번 이상 감지된 증명의 비율이다. 길이 구간은 '
        '<code>&lt;10 / 10–24 / 25–49 / 50–99 / 100–199 / ≥200</code>이며, '
        '목표 분포는 5개 출처의 고유 문자열 기준 구간 비중을 동등 평균했다. 각 출처·구간 안의 사용률을 이 분포로 재가중했다. '
        '표현 반복이 수치에 미치는 영향을 살피는 보조 계산이며, 후보를 합치거나 삭제한 것은 아니다.</p>'
        '<p><strong>활용:</strong> 모든 출처에 하나의 tactic 전략을 적용하기보다 출처별 후보를 별도로 검토할 근거다. '
        '구간 내부 길이, 정리 내용, Lean 버전과 추출 방식의 차이는 여전히 남아 있다. 성능 우열을 뜻하지 않는다.</p>'))

    rows=[[LABELS[s],f(profiles[s]['tactics']['have']['raw_percent'])+'%',
           f(profiles[s]['tactics']['have']['long_percent'])+'%',
           f(profiles[s]['tactics']['apply']['raw_percent'])+'%',
           f(profiles[s]['tactics']['apply']['long_percent'])+'%'] for s in LABELS]
    sections.append(section('selection','4. 긴 후보만 보면 중간 사실을 도입하는 증명에 치우친다',
        '<p>긴 증명에서는 중간 사실을 도입하는 <code>have</code>가 <strong>한 번 이상 등장하는 증명의 비율</strong>이 높다. '
        '전체에서는 출처별 약 20–41%이지만 200토큰 이상에서는 약 77–95%다. '
        '<code>apply</code>, <code>rw</code>, 귀납 등의 구성도 달라진다.</p>'+
        have_svg+table(['출처','have 전체','have ≥200','apply 전체','apply ≥200'],rows)+
        '<p><strong>후보군을 읽는 관점:</strong> 200토큰 하한은 후보를 탐색하기 위한 조건이다. '
        '최종 50문제의 길이 조건으로 가정하지 않으며, 짧은 후보도 함께 살펴야 한다. '
        '이 통계로 중간 사실의 개수가 더 많다고 단정하지 않는다. 긴 문자열에서는 구문이 나타날 기회 자체가 많으므로 '
        '난이도나 검증 비용 차이도 별도 확인이 필요하다.</p>'))

    warm=X['warmup_matched'];rows=[]
    for t in ['apply','induction','simp_all','grind','cases','ext','have']:
        v=[next(r for r in warm['by_control_count'][k] if r['tactic']==t) for k in ['20','50']]
        rows.append([f'<code>{t}</code>',str(v[0]['observed_of_12'])+'/12',
            f(v[0]['matched_expected'],2),f(v[1]['matched_expected'],2),
            f(v[1]['randomization_interval_95'][0],0)+'–'+f(v[1]['randomization_interval_95'][1],0)])
    sections.append(section('warmup','5. Warm-up의 apply 사용은 길이가 비슷한 후보보다 많다',
        '<p class="finding">원본 코퍼스와 비교 가능한 warm-up 12개는 <strong>모두 apply를 사용</strong>한다. '
        '같은 출처에서 길이가 비슷한 증명을 대신 뽑았을 때의 평균은 '
        '<strong>7.55–8.06개/12개</strong>였다. 비교 표본 수를 20개와 50개로 바꿔도 방향이 같다. '
        '여기의 20·50은 각 warm-up에 연결한 비교 표본의 최대 수이며 최종 50문제와는 별개의 설정이다.</p>'+
        table(['구문','실제 warm-up','가까운 20개·기대 사용 수','가까운 50개·기대 사용 수','50개 조건·모의 95% 범위'],rows)+
        '<p>각 warm-up에 대해 동일 출처·길이 비율 0.5–2 범위에서 알려진 warm-up 이름과 proof 해시를 제외하고, '
        '이 대조 계산 안에서만 같은 proof 문자열을 한 번씩 세고 로그 길이 차이가 작은 순서로 최대 20개 또는 50개를 잡았다. '
        '각 후보 집합에서 1개씩 뽑는 실험을 조건별 20,000회 반복했다. 비교 가능한 원본이 없는 PutnamBench 3개는 제외했다.</p>'
        '<p><strong>활용:</strong> warm-up만으로 전략을 고르면 apply 기반 전개에 치우칠 수 있다. '
        '반면 귀납과 simp_all은 길이를 맞춘 대조 표본의 범위 안에 들어간다. 이 점은 단순 빈도 비교로 '
        '모든 구조가 특이하다고 주장하는 것보다 더 구체적인 구분이다.</p>'
        '<p class="note">탐색적으로 18개 구문을 비교했으며, 확증적 유의성 검정은 하지 않았다. 후보 집합이 겹치고 '
        '같은 파일의 정리도 포함된다. 표본은 12개뿐이므로 최종 50문제도 같은 구성을 가질 것으로 단정하지 않는다.</p>'+
        '<details><summary>매칭 품질과 실제 후보 수</summary>'+
        table(['문제','출처','warm-up 길이','최대50 조건 후보 수','후보 길이 범위'],
            [[m['number'],LABELS[m['source']],m['length'],m['controls'],f'{m["length_min"]}–{m["length_max"]}']
             for m in warm['matching_diagnostics']])+'</details>'))

    effects=[]
    for s in LABELS:
        for v in X['file_fixed_effects'][s]:
            u=v['unique_weighted'];interval=u.get('file_bootstrap_95_percentile')
            effects.append([LABELS[s],f'<code>{v["tactic"]}</code>',u['mixed_files'],f(u['ratio'],2),
                '—' if interval is None else f(interval[0],2)+'–'+f(interval[1],2)])
    sections.append(section('appendix','부록: 같은 파일 안에서의 길이 연관성과 재현 방법',
        '<details><summary>파일 고정효과 분석 40개 결과</summary>'+
        '<p><code>log(1+증명 길이) = 파일 고정효과 + β × tactic 사용 여부</code>를 출처별·tactic별로 적합했다. '
        '고유 proof 문자열 하나의 총 가중치가 1이 되도록 빈도의 역수를 사용했다. '
        '사용·미사용 증명이 함께 있는 파일만 계수 추정에 기여한다. 표의 비율은 <code>exp(β)</code>로, '
        '길이에 1을 더한 값의 기하평균에 대한 모형상의 비율이다. 파일을 재표집해 400회 계산한 구간도 함께 적었다. '
        '혼합 파일이 5개 미만인 경우 구간을 제공하지 않는다.</p>'+
        table(['출처','tactic','혼합 파일 수','길이+1 비율','파일 재표집 95% 구간'],effects)+
        '<p class="note">파일 구성에 대한 민감도 확인이며, 무작위 모집단에서의 신뢰구간 보장은 아니다. '
        '명제 난이도와 다른 tactic을 통제하지 않았고, 긴 증명일수록 구문이 출현할 기회도 많다. '
        '어떤 tactic이 증명을 길게 만든다는 인과 주장을 할 수 없다.</p></details>'+
        '<p>모든 실험의 난수 seed는 <code>20261018</code>이다. 재현 파일은 '
        '<a href="results.json">results.json</a>, <a href="analyze.py">analyze.py</a>, '
        '<a href="verify.py">verify.py</a>, <a href="render_report.py">render_report.py</a>, '
        '<a href="validation.json">validation.json</a>에 보관한다. 원본 코퍼스와 통계 결과는 보존하고 보고서의 해석을 후보군 관점에 맞췄다.</p>'
        '<pre>python3 render_report.py # 저장된 통계로 후보군 보고서 생성</pre>'
        f'<p>실행 환경: Python {esc(X["runtime"]["python"])}, NumPy {esc(X["runtime"]["numpy"])}. '
        '입력 파일별 SHA-256과 분석 코드 해시는 results.json에 포함된다. '
        '380,489개 길이 레코드와 선언 집계를 연결하고, 긴 후보 48,519개의 proof 및 src 해시를 원문에서 재계산했다.</p>'+
        '<p>기존 데이터의 lexical/layout 추출 한계, 출처별 Lean 버전 차이, 의미적 중복 미검출 한계가 그대로 적용된다. '
        '길이와 tactic 빈도는 heartbeat 또는 검증 비용의 대체값이 아니다.</p>'))

    nav=''.join(f'<a href="#{i}">{t}</a>' for i,t in [('clones','풀이 표현 재사용'),('groups','프로젝트 구성'),('style','출처별 특징'),('selection','길이 필터'),('warmup','Warm-up'),('appendix','재현')])
    css='''*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#f5f7f8;color:#172d39;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;line-height:1.75}main{max-width:1080px;margin:auto;padding:52px 28px}header{border-bottom:2px solid #186a6b;padding-bottom:28px}h1{font-size:34px;line-height:1.3;letter-spacing:-1px;margin:8px 0 18px}h2{font-size:24px;line-height:1.4;letter-spacing:-.5px;margin:0 0 20px}p{margin:12px 0}a{color:#126768}section{margin:30px 0;padding:30px;background:white;border:1px solid #dfe6e8;border-radius:12px;scroll-margin-top:20px}.eyebrow{font-size:13px;letter-spacing:1px;color:#52717c}.lead{font-size:18px;max-width:850px}.note{color:#546972;font-size:14px}.finding{font-size:19px;border-left:4px solid #186a6b;padding:10px 20px;background:#eff7f6}nav{display:flex;gap:10px 18px;flex-wrap:wrap;margin-top:24px;font-size:14px}.table-wrap{overflow-x:auto;margin:20px 0}table{border-collapse:collapse;width:100%;font-size:14px}th{text-align:left;background:#edf4f4;font-weight:600;white-space:nowrap}td,th{padding:10px 13px;border-bottom:1px solid #e3e9eb}td{vertical-align:top;overflow-wrap:anywhere}td:first-child{min-width:75px}code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em}code{background:#eef3f4;padding:2px 4px;border-radius:3px}pre{padding:18px;background:#eef3f4;overflow-x:auto}details{margin:20px 0;border-top:1px solid #dfe6e8;padding-top:15px}summary{cursor:pointer;font-weight:600;color:#186a6b}svg{width:100%;height:auto;display:block;margin:22px 0}footer{font-size:13px;color:#546972}strong{font-weight:650}@media(max-width:650px){main{padding:24px 14px}h1{font-size:28px}h2{font-size:21px}section{padding:22px 16px}td,th{padding:9px;font-size:13px}.lead,.finding{font-size:16px}}@media print{body{background:white}main{padding:0;max-width:none}section{break-inside:avoid;padding:18px 0;border:0;border-top:1px solid #ccc}nav{display:none}a{color:inherit}details{display:block}.table-wrap{overflow:visible}svg{max-height:250px}}'''
    html_doc='<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+\
        '<title>LEArN 최종 50문제 후보군 분석 · 2026-10-18</title><style>'+css+'</style></head><body><main>'+\
        '<header><div class="eyebrow">LEArN / CORPUS DEEP DIVE / 2026-10-18</div>'+\
        '<h1>최종 50문제 후보군에는 어떤 증명들이 있는가</h1>'+\
        '<p class="lead">6개 출처에서 수집한 후보들의 길이·증명 방식·프로젝트 구성을 살펴본다. '+\
        '완성된 by 증명 32만여 개의 통계와 warm-up 비교를 통해 후보군의 특징을 정리했다.</p>'+\
        '<nav>'+nav+'</nav></header>'+''.join(sections)+\
        '<footer>2026-10-18 · 최종 50문제 후보군의 탐색적 분석 · 원본 데이터 변경 없음</footer></main></body></html>'
    (HERE/'index.html').write_text(html_doc)
    print('Created index.html and length-selection.svg')


if __name__=='__main__':main()
