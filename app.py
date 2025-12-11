import streamlit as st
import pandas as pd
from api import TarkovClient
from queries import (
    get_ammo_query, get_item_price_query, get_tasks_query, 
    get_all_crafts_query, get_items_by_category_query,    get_task_items_query,
    get_barter_items_query
)
from translations import TRANSLATIONS

# ページ設定
st.set_page_config(page_title="Tarkov Tactical Dashboard", layout="wide")

# セッション状態で言語を管理
if 'lang_code' not in st.session_state:
    st.session_state.lang_code = 'ja'

# ヘルパー関数: 翻訳取得
def t(key, *args):
    lang = st.session_state.lang_code
    text = TRANSLATIONS.get(lang, TRANSLATIONS['ja']).get(key, key)
    if args:
        return text.format(*args)
    return text

# キャッシュ: タスクIDマップ作成
@st.cache_data
def get_task_name_map(lang):
    # Trader名はなんでもよいのでダミー
    query = get_tasks_query("Any", lang=lang)
    data = TarkovClient.run_query(query)
    task_map = {}
    if data and data.get('tasks'):
        for t in data['tasks']:
            tid = str(t.get('tarkovDataId'))
            if tid and tid != "None":
                task_map[tid] = t['name']
    return task_map

# ヘルパー: 条件フォーマット
def format_requirements(reqs, task_map=None):
    if not reqs:
        return ""
    parts = []
    for r in reqs:
        if r['type'] == 'loyaltyLevel':
            parts.append(t("req_ll").format(r['value']))
        elif r['type'] == 'questCompleted':
            val = str(r['value'])
            task_name = task_map.get(val, val) if task_map else t("req_quest")
            parts.append(f"{task_name}")
    return ", ".join(parts)

# ヘルパー: 価格情報取得 (フリマ最適、トレーダー最適、条件)
def get_price_info(item, task_map=None):
    buy_for = item.get('buyFor') or []
    
    # フリマ
    flea_listing = next((x for x in buy_for if x['vendor']['name'] == 'Flea Market'), None)
    flea_price = flea_listing['price'] if flea_listing else item.get('avg24hPrice')
    
    # トレーダー (フリマ以外)
    trader_deals = [x for x in buy_for if x['vendor']['name'] != 'Flea Market']
    trader_info = None
    
    if trader_deals:
        # 価格があるものだけで最安を探す
        valid_deals = [x for x in trader_deals if x.get('price') is not None]
        if valid_deals:
            best_deal = min(valid_deals, key=lambda x: x['price'])
            req_str = format_requirements(best_deal.get('requirements', []), task_map)
            trader_info = {
                'price': best_deal['price'],
                'name': best_deal['vendor']['name'],
                'req': req_str
            }
            
    return {
        'flea_price': flea_price,
        'trader': trader_info
    }

# ヘルパー関数: アイテムの価格を算出（既存ロジックの代替: avg24hPrice -> flea -> trader）
def calculate_price(item):
    price = item.get('avg24hPrice')
    if price is None:
        info = get_price_info(item) # 名前解決不要なので task_map=None
        if info['flea_price']:
            price = info['flea_price']
        elif info['trader']:
            price = info['trader']['price']
    return price

# ヘルパー関数: 名前をAPIのnormalizedName形式（小文字ケバブケース）に変換
def normalize_name(name):
    return name.lower().replace(" ", "-")

# --- サイドバー設定 ---
st.sidebar.title(t("settings"))

# 言語切り替え
lang_option = st.sidebar.selectbox(t("language"), ["日本語", "English"], index=0 if st.session_state.lang_code == 'ja' else 1)
if lang_option == "日本語":
    st.session_state.lang_code = 'ja'
else:
    st.session_state.lang_code = 'en'

# 機能選択
feature_keys = ["ammo", "price", "task", "craft"]
feature_names = [t(f"features")[k] for k in feature_keys]
current_feature_name = st.sidebar.selectbox(t("select_feature"), feature_names)


# 選択された機能のキーを特定
current_feature = feature_keys[feature_names.index(current_feature_name)]

st.sidebar.markdown("---")
st.sidebar.caption(t("disclaimer"))
st.sidebar.markdown("[Powered by Tarkov.dev](https://tarkov.dev/)")



st.title(t("title"))

# --- 機能1: 弾薬性能チャート ---
if current_feature == "ammo":
    st.header(t(f"features")["ammo"])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        calibers = ["5.56x45mm NATO", "5.45x39mm", "7.62x39mm", "7.62x51mm NATO", ".300 Blackout", "12/70", "9x19mm Parabellum"]
        selected_caliber = st.selectbox(t("ammo_caliber"), calibers)
        
        # フィルタオプション
        with st.expander(t("filter_options"), expanded=True):
            min_pen = st.slider(t("min_penetration"), 0, 70, 0)
            min_dmg = st.slider(t("min_damage"), 0, 200, 0)

    if st.button(t("get_data")):
        # クエリ取得 (API検索用に " NATO" 等を削除しないとヒットしない場合があるが、lang指定あるのでそのまま試す)
        # ただし、日本語モードでもcaliber等の検索キーは英語のまま渡す必要がある場合が多い。
        # 今回の調査では `lang: ja` でも `name: "M855"` でヒットした。
        # しかし `categoryNames: Ammo` での検索なので、caliber が英語表記ならOK。
        # API側のcaliber名は英語表記（例: "5.56x45mm NATO"）で一致させるのが無難。
        
        query_caliber = selected_caliber.replace(" NATO", "") # 念のため
        query = get_ammo_query(query_caliber, lang=st.session_state.lang_code)
        data = TarkovClient.run_query(query)
        
        if data and data.get('items'):
            items = []
            for item in data['items']:
                props = item.get('properties') or {}
                damage = props.get('damage', 0)
                pen = props.get('penetrationPower', 0)
                frag = props.get('fragmentationChance', 0)
                
                # フィルタリング
                if damage < min_dmg or pen < min_pen:
                    continue
                
                price = calculate_price(item)
                
                if price is not None:
                    formatted_price = t("price_format").format(price)
                else:
                    formatted_price = t("not_sold")

                items.append({
                    t("col_name"): item.get('name'), # lang指定により翻訳された名前
                    t("col_damage"): damage,
                    t("col_pen"): pen,
                    t("col_frag"): f"{frag*100:.0f}%",
                    t("col_price"): formatted_price,
                    '_sorting_pen': pen # ソート用の隠し列
                })
            
            if items:
                df = pd.DataFrame(items)
                df = df.sort_values(by='_sorting_pen', ascending=False)
                df = df.drop(columns=['_sorting_pen'])
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(t("no_data"))
        else:
            st.warning(t("no_data"))

# --- 機能2: アイテム相場検索 (拡張版) ---
elif current_feature == "price":
    st.header(t(f"features")["price"])
    
    # 検索モード選択
    search_modes = {
        "keyword": t("search_mode_keyword"),
        "barter": t("search_mode_barter"),
        "ammo": t("search_mode_ammo"),
        "meds": t("search_mode_meds"),
        "task_item": t("search_mode_task_item")
    }
    mode_key = st.radio(t("search_mode_label"), list(search_modes.keys()), format_func=lambda x: search_modes[x], horizontal=True)

    # タスク名マップをロード (キャッシュ活用)
    task_map = get_task_name_map(st.session_state.lang_code)

    # 1. キーワード検索
    if mode_key == "keyword":
        search_term = st.text_input(t("search_item_placeholder"))
        if search_term:
            query = get_item_price_query(search_term, lang=st.session_state.lang_code)
            data = TarkovClient.run_query(query)
            
            if data and data.get('items'):
                for item in data['items']:
                    info = get_price_info(item, task_map)
                    flea_disp = t("price_format").format(info['flea_price']) if info['flea_price'] else t("not_sold")
                    
                    trader_str = "-"
                    if info['trader']:
                        req = f" ({info['trader']['req']})" if info['trader']['req'] else ""
                        trader_str = f"{info['trader']['name']}{req}: {t('price_format').format(info['trader']['price'])}"

                    with st.expander(f"{item['name']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric(t("flea_price"), flea_disp)
                            if item.get('link'):
                                st.markdown(f"[{t('wiki_link')}]({item['link']})")
                        with col2:
                            st.write(f"**{t('col_trader')}**")
                            st.write(trader_str)
                            
                            sell_for = item.get('sellFor', [])
                            valid_sells = [x for x in sell_for if x.get('price') is not None]
                            
                            if valid_sells:
                                best_sell = max(valid_sells, key=lambda x: x['price'])
                                price_val = best_sell['price']
                                vendor_name = best_sell['vendor']['name']
                                
                                st.write(f"---")
                                st.write(f"{t('sell_recommend')}: **{vendor_name}**")
                                st.write(f"{t('buy_price')}: {t('price_format').format(price_val)}")
            else:
                st.info(t("no_data"))

    # 1.5 バーター検索
    elif mode_key == "barter":
        search_term = st.text_input(t("search_item_placeholder"), key="barter_search")
        if search_term:
            with st.spinner(t("calculating")):
                query = get_barter_items_query(search_term, lang=st.session_state.lang_code)
                data = TarkovClient.run_query(query)
                
                if data and data.get('items'):
                    has_result = False
                    for item in data['items']:
                        b_for = item.get('bartersFor', [])
                        b_using = item.get('bartersUsing', [])
                        
                        # 両方ない場合はスキップ
                        if not b_for and not b_using:
                            continue
                        
                        has_result = True
                        with st.expander(f"{item['name']}", expanded=True):
                            col1, col2 = st.columns(2)
                            
                            # Get via Barter
                            with col1:
                                st.subheader(t("barter_get"))
                                if b_for:
                                    for b in b_for:
                                        reqs = []
                                        for r in b['requiredItems']:
                                            # アイテム名が無い場合のハンドリング（APIバグ回避）
                                            r_name = r['item']['name'] if r.get('item') else "Unknown"
                                            reqs.append(f"{r_name} x{r['count']}")
                                        req_str = " + ".join(reqs)
                                        st.markdown(f"**{b['trader']['name']}** (LL{b['level']})")
                                        st.caption(f"Cost: {req_str}")
                                        st.divider()
                                else:
                                    st.write("- None")

                            # Use as Barter
                            with col2:
                                st.subheader(t("barter_use"))
                                if b_using:
                                    for b in b_using:
                                        rews = []
                                        for r in b['rewardItems']:
                                            r_name = r['item']['name'] if r.get('item') else "Unknown"
                                            rews.append(f"{r_name} x{r['count']}")
                                        rew_str = " + ".join(rews)
                                        st.markdown(f"**{b['trader']['name']}** (LL{b['level']})")
                                        st.caption(f"Get: {rew_str}")
                                        st.divider()
                                else:
                                    st.write("- None")
                            
                            if item.get('link'):
                                st.markdown(f"[{t('wiki_link')}]({item['link']})")
                    
                    if not has_result:
                         st.info(t("no_data") + " (No barter info)")
                else:
                    st.warning(t("no_data"))

    # 2. カテゴリ検索 (弾薬 / 医薬品)
    elif mode_key in ["ammo", "meds"]:
        cats = ["Ammo"] if mode_key == "ammo" else ["Meds"]
        if st.button(t("get_data")):
            with st.spinner(t("calculating")):
                query = get_items_by_category_query(cats, lang=st.session_state.lang_code)
                data = TarkovClient.run_query(query)
                
                if data and data.get('items'):
                    rows = []
                    for item in data['items']:
                        info = get_price_info(item, task_map)
                        
                        trader_disp = "-"
                        trader_price = 0
                        if info['trader']:
                            req = f" ({info['trader']['req']})" if info['trader']['req'] else ""
                            trader_disp = f"{info['trader']['name']}{req}"
                            trader_price = info['trader']['price']
                        
                        rows.append({
                            t("col_name"): item['name'],
                            t("col_price"): info['flea_price'] if info['flea_price'] else 0, # ソート用(Flea)
                            t("flea_price"): t("price_format").format(info['flea_price']) if info['flea_price'] else t("not_sold"),
                            t("col_trader"): trader_disp,
                            t("col_trader_price"): t("price_format").format(trader_price) if trader_price else "-"
                        })
                    
                    df = pd.DataFrame(rows)
                    # 価格が高い順にソート
                    df = df.sort_values(by=t("col_price"), ascending=False)
                    st.dataframe(df[[t("col_name"), t("flea_price"), t("col_trader"), t("col_trader_price")]], use_container_width=True)
                else:
                    st.warning(t("no_data"))

    # 3. タスク用品リスト
    elif mode_key == "task_item":
        st.info("※読み込みに数秒かかる場合があります。")
        if st.button(t("get_data")):
            with st.spinner(t("calculating")):
                query = get_task_items_query(lang=st.session_state.lang_code)
                data = TarkovClient.run_query(query)
                
                if data and data.get('tasks'):
                    item_map = {}
                    
                    for task in data['tasks']:
                        for obj in task.get('objectives', []):
                            # TaskObjectiveItem 以外は item キーがない場合がある
                            item = obj.get('item')
                            if not item:
                                continue
                            
                            i_name = item['name']
                            if i_name not in item_map:
                                item_map[i_name] = {
                                    'obj': item,
                                    'total_count': 0,
                                    'fir_count': 0,
                                    'tasks': set(),
                                    'task_traders': set()
                                }
                            
                            count = obj.get('count', 1)
                            item_map[i_name]['total_count'] += count
                            if obj.get('foundInRaid'):
                                item_map[i_name]['fir_count'] += count
                            item_map[i_name]['tasks'].add(task['name'])
                            item_map[i_name]['task_traders'].add(task['trader']['name'])
                    
                    rows = []
                    for name, item_entry in item_map.items():
                        obj = item_entry['obj']
                        info = get_price_info(obj, task_map)
                        
                        trader_disp = "-"
                        if info['trader']:
                            req = f" ({info['trader']['req']})" if info['trader']['req'] else ""
                            trader_disp = f"{info['trader']['name']}{req}: {t('price_format').format(info['trader']['price'])}"

                        rows.append({
                            t("col_name"): name,
                            t("col_task_trader"): ", ".join(sorted(item_entry['task_traders'])),
                            t("task_item_count"): item_entry['total_count'],
                            t("task_item_fir"): item_entry['fir_count'],
                            t("col_price"): info['flea_price'] if info['flea_price'] else 0,
                            t("flea_price"): t("price_format").format(info['flea_price']) if info['flea_price'] else t("not_sold"),
                            t("col_trader"): trader_disp
                        })
                        
                    if rows:
                        df = pd.DataFrame(rows)
                        # タスク使用数が多い順 -> 価格順
                        df = df.sort_values(by=[t("task_item_count"), t("col_price")], ascending=[False, False])
                        st.dataframe(df[[t("col_name"), t("col_task_trader"), t("task_item_count"), t("task_item_fir"), t("flea_price"), t("col_trader")]], use_container_width=True)
                    else:
                        st.warning(t("no_data"))

# --- 機能3: タスク検索 ---
elif current_feature == "task":
    st.header(t(f"features")["task"])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        traders = ["Prapor", "Therapist", "Fence", "Skier", "Peacekeeper", "Mechanic", "Ragman", "Jaeger"]
        target_trader = st.selectbox(t("trader"), traders)
        
        # フィルタ
        with st.expander(t("filter_options"), expanded=True):
            maps = ["Ground Zero", "Streets of Tarkov", "Customs", "Factory", "Woods", "Reserve", "Lighthouse", "Shoreline", "Interchange", "Labs", "Any"]
            selected_maps = st.multiselect(t("map_filter"), maps)
            
            max_level = st.slider(t("level_filter", 50), 1, 70, 40)
            
            search_task_item = st.text_input(t("item_filter"))
    
    if st.button(t("get_data")):
        query = get_tasks_query(target_trader, lang=st.session_state.lang_code)
        data = TarkovClient.run_query(query)
        
        if data and data.get('tasks'):
            tasks = []
            for t_obj in data['tasks']:
                # トレーダーフィルタ (normalizedNameを使用)
                if t_obj['trader']['normalizedName'] != normalize_name(target_trader):
                    continue
                    
                # マップフィルタ
                task_map = t_obj.get('map')
                map_name = task_map['name'] if task_map else "Any"
                if selected_maps:     
                   if map_name not in selected_maps and "Any" not in selected_maps:
                       continue
                
                # レベルフィルタ
                min_level = t_obj.get('minPlayerLevel') or 0
                if min_level > max_level:
                    continue
                
                # テキストフィルタ (アイテム名などを想定して全テキスト検索)
                if search_task_item:
                    search_lower = search_task_item.lower()
                    name_match = search_lower in t_obj['name'].lower()
                    desc_match = False
                    for obj in t_obj.get('objectives', []):
                         if search_lower in obj.get('description', '').lower():
                             desc_match = True
                             break
                    if not (name_match or desc_match):
                        continue
                
                tasks.append({
                    'name': t_obj['name'],
                    'map': map_name,
                    'objectives': t_obj.get('objectives', []),
                    'wikiLink': t_obj.get('wikiLink')
                })
            
            if not tasks:
                 st.info(t("no_data"))
            else:
                for task in tasks:
                    with st.expander(f"{task['name']} ({task['map']})"):
                        st.markdown(f"**{t('task_objective')}:**")
                        for obj in task['objectives']:
                            st.write(f"- {obj.get('description')}")
                        
                        if task['wikiLink']:
                            st.markdown(f"[{t('wiki_link')}]({task['wikiLink']})")
        else:
             st.warning(t("no_data"))

# --- 機能4: クラフト利益計算 ---
elif current_feature == "craft":
    st.header(t(f"features")["craft"])
    
    col1, col2 = st.columns([1, 2])
    with col1:
        stations = ["Workbench", "Lavatory", "Medstation", "Nutrition Unit", "Water Collector", "Booze Generator", "Intelligence Center"]
        target_station = st.selectbox(t("station"), stations)
        
        # フィルタ・オプション
        with st.expander(t("filter_options"), expanded=True):
            max_station_level = st.slider(t("level_station_filter", 3), 1, 3, 3)
            filter_item_name = st.text_input(t("item_filter"))
            exclude_loss = st.checkbox(t("exclude_loss"), value=True)
            
            sort_options = {
                "profit": t("sort_profit"),
                "hourly": t("sort_hourly"),
                "time": t("sort_time")
            }
            sort_by = st.selectbox(t("sort_order"), list(sort_options.keys()), format_func=lambda x: sort_options[x])
    
    if st.button(t("calculate")):
        with st.spinner(t("calculating")):
            query = get_all_crafts_query(lang=st.session_state.lang_code)
            data = TarkovClient.run_query(query)
            
            if data and data.get('crafts'):
                results = []
                
                for craft in data['crafts']:
                    # ステーションフィルタ (normalizedNameを使用)
                    if craft['station']['normalizedName'] != normalize_name(target_station):
                        continue
                    
                    # レベルフィルタ
                    level = craft.get('level') or 0
                    if level > max_station_level:
                        continue
                        
                    # 報酬（完成品）計算
                    total_revenue = 0
                    reward_names = []
                    reward_search_str = ""
                    
                    for reward in craft.get('rewardItems', []):
                        item = reward['item']
                        count = reward['count']
                        price = calculate_price(item) or 0
                        total_revenue += price * count
                        reward_names.append(f"{item['name']} x{count}")
                        reward_search_str += item['name'] + " "
                        
                    # アイテム名フィルタ
                    if filter_item_name:
                         if filter_item_name.lower() not in reward_search_str.lower():
                             continue
                        
                    # コスト（材料）計算
                    total_cost = 0
                    required_names = []
                    
                    for req in craft.get('requiredItems', []):
                        item = req['item']
                        count = req['count']
                        price = calculate_price(item) or 0
                        total_cost += price * count
                        required_names.append(f"{item['name']} x{count}")
                        
                    profit = total_revenue - total_cost
                    
                    # 赤字除外
                    if exclude_loss and profit < 0:
                        continue
                    
                    duration_sec = craft.get('duration') or 1
                    profit_per_hour = (profit / duration_sec) * 3600
                    
                    results.append({
                        t("col_product"): ", ".join(reward_names),
                        t("col_material"): ", ".join(required_names),
                        t("col_revenue"): f"{int(total_revenue):,}", # 表示用
                        t("col_cost"): f"{int(total_cost):,}",
                        t("col_profit"): int(profit), # ソート用兼表示用
                        t("col_time"): f"{duration_sec / 60:.0f} min",
                        t("col_profit_per_hour"): int(profit_per_hour),
                        
                        # ソート用数値
                        '_sort_profit': profit,
                        '_sort_hourly': profit_per_hour,
                        '_sort_time': duration_sec
                    })
                
                if results:
                    df = pd.DataFrame(results)
                    
                    # ソート適用
                    if sort_by == "profit":
                        df = df.sort_values(by='_sort_profit', ascending=False)
                    elif sort_by == "hourly":
                        df = df.sort_values(by='_sort_hourly', ascending=False)
                    elif sort_by == "time":
                        df = df.sort_values(by='_sort_time', ascending=True)
                        
                    # 表示用カラムの整形（数値カラムにフォーマット適用）
                    df[t("col_profit")] = df['_sort_profit'].apply(lambda x: f"{int(x):,} ₽")
                    df[t("col_profit_per_hour")] = df['_sort_hourly'].apply(lambda x: f"{int(x):,} ₽/h")

                    # 不要なカラムを削除
                    display_cols = [t("col_product"), t("col_material"), t("col_revenue"), t("col_cost"), t("col_profit"), t("col_time"), t("col_profit_per_hour")]
                    st.write(f"**{target_station}** (Lv.{max_station_level})")
                    st.dataframe(df[display_cols], use_container_width=True)
                else:
                    st.info(t("no_data"))
            else:
                 st.warning(t("no_data"))
