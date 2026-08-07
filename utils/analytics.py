# utils/analytics.py
import streamlit as st
import time
import json
from datetime import datetime
import pandas as pd
from collections import defaultdict

class UXMonitor:
    def __init__(self):
        # Inicializa estrutura de dados
        if 'analytics' not in st.session_state:
            st.session_state.analytics = {
                'events': [],
                'sessions': [],
                'page_timers': {},
                'page_views_tracked': set(),  # Para evitar duplicatas
                'ai_calls_tracked': set(),    # Para evitar duplicatas de IA
                'session_id': self._generate_session_id()
            }
    
    def _generate_session_id(self):
        """Gera um ID único para a sessão"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def track_event(self, event_type, page, metadata=None, deduplicate=True):
        """
        Registra um evento do usuário com controle de duplicatas
        
        Args:
            event_type: page_view, click, export, ai_call, error, delete, ai_generation
            page: nome da página
            metadata: dados adicionais
            deduplicate: se True, evita duplicatas em sequência
        """
        # Prevenção de duplicatas para page_view
        if event_type == 'page_view' and deduplicate:
            # Cria uma chave única para a página na sessão
            page_key = f"{page}_{st.session_state.analytics['session_id']}"
            
            # Se já registrou esta página nesta sessão, não conta de novo
            if page_key in st.session_state.analytics['page_views_tracked']:
                # Mas ainda registra o evento como "page_revisit" (menos relevante)
                event_type = 'page_revisit'
            else:
                st.session_state.analytics['page_views_tracked'].add(page_key)
        
        # Prevenção de duplicatas para AI calls
        if event_type == 'ai_call' and deduplicate:
            # Cria uma chave baseada no conteúdo
            content_hash = self._get_content_hash(metadata)
            if content_hash:
                ai_key = f"{page}_{content_hash}_{st.session_state.analytics['session_id']}"
                
                # Se já chamou a IA para este conteúdo, não conta de novo
                if ai_key in st.session_state.analytics['ai_calls_tracked']:
                    return  # Ignora completamente
                else:
                    st.session_state.analytics['ai_calls_tracked'].add(ai_key)
        
        # Registra o evento
        event = {
            'timestamp': datetime.now().isoformat(),
            'session_id': st.session_state.analytics['session_id'],
            'event_type': event_type,
            'page': page,
            'metadata': metadata or {},
            'user_agent': st.query_params.get('ua', 'unknown')
        }
        
        st.session_state.analytics['events'].append(event)
        
        # Marca tempo de página (apenas para page_view verdadeiro)
        if event_type == 'page_view':
            st.session_state.analytics['page_timers'][page] = time.time()
    
    def _get_content_hash(self, metadata):
        """Gera um hash do conteúdo para identificar duplicatas de IA"""
        if not metadata:
            return None
        
        # Pega campos relevantes para identificar duplicatas
        relevant_fields = {}
        for key in ['field', 'prompt', 'content_length', 'section']:
            if key in metadata:
                relevant_fields[key] = metadata[key]
        
        if not relevant_fields:
            return None
        
        # Gera hash
        import hashlib
        content_str = json.dumps(relevant_fields, sort_keys=True)
        return hashlib.md5(content_str.encode()).hexdigest()[:16]
    
    def track_page_time(self, page):
        """Calcula o tempo gasto em uma página (chamado quando o usuário sai)"""
        if page in st.session_state.analytics['page_timers']:
            start_time = st.session_state.analytics['page_timers'].pop(page)
            duration = time.time() - start_time
            
            # Só registra se o tempo for significativo (> 2 segundos)
            if duration > 2:
                self.track_event('page_duration', page, {'seconds': round(duration, 2)}, deduplicate=False)
    
    def track_error(self, page, error_type, error_msg):
        """Registra erros com limite para não poluir"""
        # Limita erros para não encher o log
        error_key = f"{page}_{error_type}"
        error_count = sum(1 for e in st.session_state.analytics['events'] 
                         if e.get('metadata', {}).get('error_type') == error_type 
                         and e.get('page') == page)
        
        if error_count < 10:  # Máximo de 10 erros do mesmo tipo por sessão
            self.track_event('error', page, {
                'error_type': error_type,
                'message': str(error_msg)[:100]  # Limita mensagem
            }, deduplicate=False)
    
    def track_ai_generation(self, page, field, items_count):
        """Tracking específico para gerações de IA (múltiplos itens)"""
        self.track_event('ai_generation', page, {
            'field': field,
            'items_generated': items_count,
            'timestamp': datetime.now().isoformat()
        }, deduplicate=True)  # Deduplica por campo e conteúdo
    
    def track_interaction(self, page, action_type, field=None):
        """Tracking genérico para interações do usuário (cliques, edições, etc)"""
        # Agrupa interações similares para não poluir
        interaction_key = f"{page}_{action_type}_{field}"
        
        # Verifica se já registrou esta interação recentemente (< 5 segundos)
        recent_events = [e for e in st.session_state.analytics['events'][-10:] 
                        if e.get('event_type') == 'interaction' 
                        and e.get('page') == page 
                        and e.get('metadata', {}).get('action') == action_type]
        
        if recent_events:
            last_event = recent_events[-1]
            last_time = datetime.fromisoformat(last_event['timestamp'])
            if (datetime.now() - last_time).total_seconds() < 5:
                return  # Ignora interações repetidas em menos de 5 segundos
        
        self.track_event('interaction', page, {
            'action': action_type,
            'field': field
        }, deduplicate=False)
    
    def get_insights(self):
        """Gera insights agregados com dados mais limpos"""
        df = pd.DataFrame(st.session_state.analytics['events'])
        if df.empty:
            return "Ainda não há dados suficientes."
        
        insights = []
        
        # 1. Páginas mais acessadas (apenas page_view verdadeiro)
        page_views = df[df.event_type == 'page_view'].page.value_counts()
        if not page_views.empty:
            insights.append(f"📊 Páginas mais acessadas:\n{page_views.head(3).to_string()}")
        
        # 2. Gerações de IA (agrupado)
        ai_generations = df[df.event_type == 'ai_generation']
        if not ai_generations.empty:
            total_items = ai_generations['metadata'].apply(lambda x: x.get('items_generated', 0)).sum()
            insights.append(f"🤖 Itens gerados por IA: {total_items} em {len(ai_generations)} chamadas")
        
        # 3. Interações do usuário (filtradas)
        interactions = df[df.event_type == 'interaction']
        if not interactions.empty:
            top_actions = interactions['metadata'].apply(lambda x: x.get('action', 'unknown')).value_counts()
            insights.append(f"🖱️ Ações mais comuns: {top_actions.head(3).to_string()}")
        
        return "\n\n".join(insights)
