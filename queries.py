def get_ammo_query(caliber: str, lang: str = "ja") -> str:
    """
    指定された口径の弾薬情報を取得するクエリを生成します。
    """
    return f"""
    {{
        items(categoryNames: Ammo, name: "{caliber}", lang: {lang}) {{
            name
            shortName
            avg24hPrice
            buyFor {{
                price
                vendor {{
                    name
                }}
                requirements {{
                    type
                    value
                }}
            }}
            properties {{
                ... on ItemPropertiesAmmo {{
                    damage
                    penetrationPower
                    fragmentationChance
                }}
            }}
        }}
    }}
    """

def get_item_price_query(search_term: str, lang: str = "ja") -> str:
    """
    アイテム名を検索して価格情報を取得するクエリを生成します。
    """
    return f"""
    {{
        items(name: "{search_term}", lang: {lang}) {{
            name
            shortName
            avg24hPrice
            buyFor {{
                price
                vendor {{
                    name
                }}
                requirements {{
                    type
                    value
                }}
            }}
            sellFor {{
                price
                vendor {{
                    name
                }}
            }}
            link
        }}
    }}
    """

def get_tasks_query(trader_name: str, lang: str = "ja") -> str:
    """
    指定されたトレーダーのタスク一覧を取得するクエリ。
    """
    return f"""
    {{
        tasks(limit: 1000, lang: {lang}) {{
            name
            tarkovDataId
            minPlayerLevel
            trader {{
                name
                normalizedName
            }}
            map {{
                name
            }}
            objectives {{
                description
            }}
            wikiLink
        }}
    }}
    """

def get_all_crafts_query(lang: str = "ja") -> str:
    """
    全てのクラフトレシピと価格情報を取得するクエリ。
    特定ステーションのフィルタリングはクライアント側で行う。
    """
    return f"""
    {{
        crafts(lang: {lang}) {{
            station {{
                name
                normalizedName
            }}
            level
            duration
            rewardItems {{
                count
                item {{
                    name
                    shortName
                    avg24hPrice
                    buyFor {{
                        price
                        vendor {{
                            name
                        }}
                    }}
                }}
            }}
            requiredItems {{
                count
                item {{
                    name
                    shortName
                    avg24hPrice
                    buyFor {{
                        price
                        vendor {{
                            name
                        }}
                    }}
                }}
            }}
        }}
    }}
    """

def get_items_by_category_query(category_names: list[str], lang: str = "ja") -> str:
    """
    指定されたカテゴリのアイテム一覧を取得するクエリ。
    """
    # カテゴリリストをGraphQLのEnum形式文字列に変換 (例: [Ammo, Meds])
    cats_str = ", ".join(category_names)
    
    return f"""
    {{
        items(categoryNames: [{cats_str}], limit: 100, lang: {lang}) {{
            name
            shortName
            avg24hPrice
            buyFor {{
                price
                vendor {{
                    name
                }}
                requirements {{
                    type
                    value
                }}
            }}
            sellFor {{
                price
                vendor {{
                    name
                }}
            }}
            link
        }}
    }}
    """

def get_task_items_query(lang: str = "ja") -> str:
    """
    タスクで使用されるアイテム（納品目標）を取得するクエリ。
    """
    return f"""
    {{
        tasks(limit: 200, lang: {lang}) {{
            name
            trader {{
                name
            }}
            objectives {{
                ... on TaskObjectiveItem {{
                    item {{
                        name
                        shortName
                        avg24hPrice
                        buyFor {{
                            price
                            vendor {{
                                name
                            }}
                            requirements {{
                                type
                                value
                            }}
                        }}
                        link
                    }}
                    count
                    foundInRaid
                }}
            }}
        }}
    }}
    """

def get_barter_items_query(search_term: str, lang: str = "ja") -> str:
    """
    指定されたアイテム名に関連するバーター情報を取得するクエリ。
    入手(bartersFor)と素材利用(bartersUsing)の両方を取得。
    """
    return f"""
    {{
        items(name: "{search_term}", lang: {lang}, limit: 20) {{
            name
            shortName
            link
            bartersFor {{
                trader {{
                    name
                }}
                level
                requiredItems {{
                    count
                    item {{
                        name
                        shortName
                    }}
                }}
            }}
            bartersUsing {{
                trader {{
                    name
                }}
                level
                rewardItems {{
                    count
                    item {{
                        name
                        shortName
                    }}
                }}
            }}
        }}
    }}
    """
