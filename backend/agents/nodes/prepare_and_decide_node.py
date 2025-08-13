# Prepare-and-decide: local context → gate → optional Tavily → unified context + citations
import json, logging
from heapq import nlargest
from urllib.parse import urlparse
from typing import Any, Dict, List
from langchain_community.retrievers import TavilySearchAPIRetriever
from langchain_core.messages import SystemMessage
from utils.config import Config

log = logging.getLogger("chatbot-server")
class PrepareAndDecideNode:
    def __init__(self, min_local_chars=200, min_local_hits=3, max_local_chunks=5, tavily_k=5, max_total_chars=6000, llm=None):
        self.min_local_chars=min_local_chars; self.min_local_hits=min_local_hits
        self.max_local_chunks=max_local_chunks; self.max_total_chars=max_total_chars
        self._tavily_k=tavily_k; self._retriever=None; self._llm=llm
    @property
    def retriever(self): 
        if not self._retriever: self._retriever=TavilySearchAPIRetriever(k=self._tavily_k)
        return self._retriever
    @staticmethod
    def _q(msgs: List[Any]) -> str:
        return next((c.strip() for m in reversed(msgs or []) if (c:=getattr(m,"content",None)) and isinstance(c,str) and c.strip()), "")
    @staticmethod
    def _dom(u: str|None) -> str:
        try: return urlparse(u or "").netloc
        except: return ""
    @staticmethod
    def _date(meta: Dict[str,Any]) -> str:
        return ""

    async def execute(self, state: Dict[str,Any]) -> Dict[str,Any]:
        q=self._q(state.get("messages",[])); ql=q.lower()
        chunks=nlargest(self.max_local_chunks,[c for c in (state.get("rag_chunks") or []) if isinstance(c,str) and c],key=len)
        hits=sum(len(c)>=self.min_local_chars for c in chunks)
        needs_web=not(hits>=self.min_local_hits)
        log.info("Gate:%s hits=%d","insufficient" if needs_web else "sufficient",hits)
        parts=(["Local context:"]+chunks) if chunks else []; cites: List[Dict[str,Any]]=[]
        if Config.ENABLE_REACT_JUDGER and self._llm and needs_web:
            try:
                prompt=(f"You are a concise analyst. Should we web-search beyond local context?\nQ:{q}\n"
                        f"Local_hits(≥{self.min_local_chars}):{hits}\n"
                        'Respond JSON: {"needs_web":true|false,"why":"...","queries":["q1","q2"]}')
                r=await self._llm.ainvoke([SystemMessage(content=prompt)])
                js=json.loads(getattr(r,"content","") or "{}"); needs_web=bool(js.get("needs_web",needs_web))
                state["reasoning"]=str(js.get("why","")); q=(js.get("queries") or [q])[0] or q
            except Exception as e: log.debug("Judger error:%s",e)
        if needs_web and q:
            try: docs=self.retriever.invoke(q) or []
            except Exception as e: log.warning("Web retrieval failed:%s",e); docs=[]
            log.info("Web snippets=%d",len(docs))
            if docs:
                parts.append("Web sources:"); parts.extend(d.page_content for d in docs[:8] if getattr(d,"page_content",None))
                for d in docs[:8]:
                    meta=getattr(d,"metadata",{}) or {}; url=meta.get("source") or meta.get("url"); title=meta.get("title")
                    if url or title: cites.append({"url":url,"title":title,"domain":self._dom(url)})
        ctx="\n".join(parts)[:self.max_total_chars]; seen=set()
        dedup=[c for c in cites if (k:=c.get("url") or (c.get("title"),c.get("domain"))) and not (k in seen or seen.add(k))]
        return {"context":ctx,"citations":dedup}
