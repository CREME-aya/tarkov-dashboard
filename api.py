import requests
import streamlit as st
from typing import Optional, Dict, Any

API_URL = 'https://api.tarkov.dev/graphql'

class TarkovClient:
    """Tarkov.dev APIと通信するためのクライアントクラス。"""

    @staticmethod
    def run_query(query: str) -> Optional[Dict[str, Any]]:
        """
        GraphQLクエリを実行し、結果を返します。
        
        Args:
            query (str): 実行するGraphQLクエリ文字列。
            
        Returns:
            Optional[Dict[str, Any]]: クエリ結果の辞書。エラーが発生した場合はNone。
        """
        try:
            response = requests.post(API_URL, json={'query': query})
            response.raise_for_status() # HTTPエラーチェック
            
            data = response.json()
            
            # GraphQLのエラーチェック
            if 'errors' in data:
                error_msg = data['errors'][0].get('message', 'Unknown GraphQL error')
                st.error(f"API Error: {error_msg}")
                return None
                
            # データが存在するかチェック
            if 'data' not in data:
                st.error("API response missing 'data' field.")
                return None
                
            return data['data']
            
        except requests.exceptions.RequestException as e:
            st.error(f"Network Error: {e}")
            return None
        except ValueError as e: # JSONデコードエラーなど
            st.error(f"Data Error: {e}")
            return None
