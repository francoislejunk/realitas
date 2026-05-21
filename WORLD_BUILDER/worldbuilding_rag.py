"""
Worldbuilding RAG System - Single Source for Categories + RAG Engine

This file contains:
1. WorldbuildingCategory enum - All category definitions
2. WorldbuildingRAGSystem class - The RAG engine for storing/searching lore
3. Helper classes (SimpleEmbedder, WorldbuildingDocument)

Lore content is stored separately in penumbra_lore.py
"""

import json
import logging
import os
import numpy as np
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter


# ============================================================================
# WORLDBUILDING CATEGORIES
# ============================================================================

class WorldbuildingCategory(Enum):
    """All worldbuilding categories for the RAG system
    
    Categories are organized into logical groups:
    - Core World: Structure, temporal, beings, supernatural
    - Society: Civilization, factions, relationships, conflicts
    - Narrative: Culture, narration style, expansion
    - Systems: Mechanics, places
    - Actor Generation: UA, NUA, INUA specific guidelines
    """
    
    # CORE WORLD
    WORLD_STRUCTURE = "world_structure"      # Geography, environment, weather
    TEMPORAL = "temporal"                     # History, timelines, current era
    BEINGS = "beings"                         # Species, character types
    SUPERNATURAL = "supernatural"             # Magic/powers (or lack thereof)
    
    # SOCIETY
    CIVILIZATION = "civilization"             # Technology, social classes, economy
    FACTIONS_ORGANIZATIONS = "factions_organizations"  # Groups, factions
    RELATIONSHIP_MATRICES = "relationship_matrices"    # Social dynamics
    NUA_RELATIONSHIP_MATRICES = "nua_relationship_matrices"  # Social dynamics for NUAs
    MNUA_RELATIONSHIP_MATRICES = "mnua_relationship_matrices"  # Social dynamics for MNUAs
    CONFLICT_GENERATORS = "conflict_generators"        # Sources of tension
    
    # NARRATIVE
    CULTURE = "culture"                       # Customs, language, atmosphere
    NARRATION_STYLE_TONE = "narration_style_tone"  # Storytelling approach
    EXPANSION_SEEDS = "expansion_seeds"       # Future content hooks
    
    # SYSTEMS
    MECHANICS = "mechanics"                   # Game rules, systems
    PLACES = "places"                         # Locations, POIs
    CITIES = "cities"                         # Major cities and settlements
    
    # ACTOR GENERATION - Specific guidelines for each actor type
    UA_GENERATION = "ua_generation"           # User Actor generation
    NUA_GENERATION = "nua_generation"         # Non-User Actor generation
    MNUA_GENERATION = "mnua_generation"       # Major Non-User Actor generation (recurring important NPCs)
    INUA_GENERATION = "inua_generation"       # Inanimate NUA generation

    # ACTOR-SPECIFIC ROLE DATA
    UA_OCCUPATIONS = "ua_occupations"         # UA-appropriate occupations/archetypes
    NUA_OCCUPATIONS = "nua_occupations"       # Common NPC occupations/archetypes
    MNUA_OCCUPATIONS = "mnua_occupations"     # Major NPC occupations/archetypes
    UA_GOALS = "ua_goals"                     # UA goal patterns and examples
    NUA_GOALS = "nua_goals"                   # NUA goal patterns and examples
    MNUA_GOALS = "mnua_goals"                 # MNUA goal patterns and examples

    # EXPLICIT GOAL LIBRARIES (STRICT WHITELISTS)
    # These are intended for hard-RAG-lock Mode A goal selection.
    GOALS_UA = "goals_ua"                      # Explicit UA goal library (pick exact goal lines)
    GOALS_NUA = "goals_nua"                    # Explicit NUA goal library (pick exact goal lines)
    GOALS_MNUA = "goals_mnua"                  # Explicit MNUA goal library (pick exact goal lines)
    
    # FACTION-SPECIFIC ACTOR GENERATION - Factions available for each actor type
    FACTION_UA = "faction_ua"                 # Factions available for User Actors
    FACTION_NUA = "faction_nua"               # Factions available for Non-User Actors
    FACTION_MNUA = "faction_mnua"             # Factions available for Major Non-User Actors
    
    # WORLD SIMULATION - Living world elements
    ENVIRONMENTAL_HAZARDS = "environmental_hazards"  # Hazards, dangers, environmental events
    WORLD_EVENTS = "world_events"             # Background events, NUA interactions, ambient occurrences


# Category descriptions for documentation/UI
CATEGORY_DESCRIPTIONS = {
    WorldbuildingCategory.WORLD_STRUCTURE:
        "Physical world structure including geography, biomes, landmarks, climate, weather patterns.",
    
    WorldbuildingCategory.TEMPORAL:
        "Temporal structure covering history, current events, timelines, and era-specific details.",
    
    WorldbuildingCategory.BEINGS:
        "All intelligent beings including species, character types, and general NPC archetypes.",
    
    WorldbuildingCategory.SUPERNATURAL:
        "Supernatural elements (or lack thereof) - magic systems, powers, mysteries.",
    
    WorldbuildingCategory.CIVILIZATION:
        "Societal structures including technology, political systems, social classes, economy.",
    
    WorldbuildingCategory.FACTIONS_ORGANIZATIONS:
        "Groups with ideologies, goals, and conflicting interests.",
    
    WorldbuildingCategory.RELATIONSHIP_MATRICES:
        "How different factions, characters, and locations relate to each other.",

    WorldbuildingCategory.NUA_RELATIONSHIP_MATRICES:
        "Relationship and social-dynamics guidance specific to Non-User Actors (NUA).",

    WorldbuildingCategory.MNUA_RELATIONSHIP_MATRICES:
        "Relationship and social-dynamics guidance specific to Major Non-User Actors (MNUA).",
    
    WorldbuildingCategory.CONFLICT_GENERATORS:
        "Sources of tension and conflict in the world.",
    
    WorldbuildingCategory.CULTURE:
        "Cultural identity including customs, traditions, language, sensory/atmospheric details.",
    
    WorldbuildingCategory.NARRATION_STYLE_TONE:
        "Storytelling approaches, descriptive frameworks, narrative voice.",
    
    WorldbuildingCategory.EXPANSION_SEEDS:
        "Framework for future content that maintains world consistency.",
    
    WorldbuildingCategory.MECHANICS:
        "Game mechanics and rules integration with worldbuilding.",
    
    WorldbuildingCategory.PLACES:
        "Specific locations, points of interest, and their characteristics.",
    
    WorldbuildingCategory.CITIES:
        "Major cities and settlements - their districts, rulers, politics, atmosphere, and notable features.",
    
    WorldbuildingCategory.UA_GENERATION:
        "Guidelines for generating User Actors - names, skills, backgrounds, goals.",
    
    WorldbuildingCategory.NUA_GENERATION:
        "Guidelines for generating Non-User Actors - NPCs, their roles, personalities.",
    
    WorldbuildingCategory.MNUA_GENERATION:
        "Guidelines for generating Major Non-User Actors - important recurring characters with enhanced depth, UA-level complexity, tension modifiers, and narrative significance.",
    
    WorldbuildingCategory.INUA_GENERATION:
        "Guidelines for generating Inanimate Non-User Actors - objects, items, interactables.",

    WorldbuildingCategory.UA_OCCUPATIONS:
        "UA-appropriate occupations and archetypes (player-facing roles) for this setting.",

    WorldbuildingCategory.NUA_OCCUPATIONS:
        "Common NPC occupations and archetypes for this setting.",

    WorldbuildingCategory.MNUA_OCCUPATIONS:
        "Major NPC occupations and archetypes (recurring roles with higher narrative weight) for this setting.",

    WorldbuildingCategory.UA_GOALS:
        "Goal patterns and examples appropriate for User Actors in this setting.",

    WorldbuildingCategory.NUA_GOALS:
        "Goal patterns and examples appropriate for Non-User Actors in this setting.",

    WorldbuildingCategory.MNUA_GOALS:
        "Goal patterns and examples appropriate for Major Non-User Actors in this setting.",
    
    WorldbuildingCategory.FACTION_UA:
        "Factions available for User Actors - clans, organizations, affiliations the player can belong to.",
    
    WorldbuildingCategory.FACTION_NUA:
        "Factions available for Non-User Actors - clans, organizations, affiliations for regular NPCs.",
    
    WorldbuildingCategory.FACTION_MNUA:
        "Factions available for Major Non-User Actors - clans, organizations for important recurring characters.",
    
    WorldbuildingCategory.ENVIRONMENTAL_HAZARDS:
        "Environmental hazards, dangers, and events that can occur in different locations - machinery failures, structural collapses, weather events, etc.",
    
    WorldbuildingCategory.WORLD_EVENTS:
        "Background world events, NUA-to-NUA interactions, ambient occurrences that make the world feel alive.",
}


def get_category_display_name(category: WorldbuildingCategory) -> str:
    """Get human-readable display name for a category"""
    return category.value.replace('_', ' ').title()


# ============================================================================
# SIMPLE EMBEDDER - Text embedding without external dependencies
# ============================================================================

class SimpleEmbedder:
    """Simple text embedding using character n-grams and TF-IDF-like weighting"""
    
    def __init__(self, ngram_size: int = 3, vocab_size: int = 1000):
        self.ngram_size = ngram_size
        self.vocab_size = vocab_size
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        
    def _get_ngrams(self, text: str) -> List[str]:
        """Extract character n-grams from text"""
        text = text.lower()
        return [text[i:i+self.ngram_size] for i in range(len(text) - self.ngram_size + 1)]
    
    def fit(self, documents: List[str]):
        """Build vocabulary from documents"""
        all_ngrams = []
        doc_ngrams = []
        
        for doc in documents:
            ngrams = self._get_ngrams(doc)
            doc_ngrams.append(set(ngrams))
            all_ngrams.extend(ngrams)
        
        # Build vocabulary from most common ngrams
        ngram_counts = Counter(all_ngrams)
        most_common = ngram_counts.most_common(self.vocab_size)
        self.vocab = {ngram: idx for idx, (ngram, _) in enumerate(most_common)}
        
        # Calculate IDF
        num_docs = len(documents)
        for ngram in self.vocab:
            doc_freq = sum(1 for doc_ng in doc_ngrams if ngram in doc_ng)
            self.idf[ngram] = np.log(num_docs / (1 + doc_freq))
    
    def embed(self, text: str) -> np.ndarray:
        """Convert text to embedding vector"""
        ngrams = self._get_ngrams(text)
        vector = np.zeros(self.vocab_size)
        
        ngram_counts = Counter(ngrams)
        
        for ngram, count in ngram_counts.items():
            if ngram in self.vocab:
                idx = self.vocab[ngram]
                tf = count / len(ngrams) if ngrams else 0
                vector[idx] = tf * self.idf.get(ngram, 1.0)
        
        # Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector


# ============================================================================
# WORLDBUILDING DOCUMENT - Data structure for lore entries
# ============================================================================

@dataclass
class WorldbuildingDocument:
    """A single piece of worldbuilding lore with metadata"""
    doc_id: str
    title: str
    content: str
    category: WorldbuildingCategory
    subcategory: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    importance: int = 5  # 1-10 scale
    related_docs: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            'doc_id': self.doc_id,
            'title': self.title,
            'content': self.content,
            'category': self.category.value,
            'subcategory': self.subcategory,
            'tags': self.tags,
            'importance': self.importance,
            'related_docs': self.related_docs,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'embedding': self.embedding.tolist() if self.embedding is not None else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorldbuildingDocument':
        """Create from dictionary"""
        embedding = np.array(data['embedding']) if data.get('embedding') else None
        return cls(
            doc_id=data['doc_id'],
            title=data['title'],
            content=data['content'],
            category=WorldbuildingCategory(data['category']),
            subcategory=data.get('subcategory'),
            tags=data.get('tags', []),
            importance=data.get('importance', 5),
            related_docs=data.get('related_docs', []),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            embedding=embedding
        )


# ============================================================================
# WORLDBUILDING RAG SYSTEM - The main RAG engine
# ============================================================================

class WorldbuildingRAGSystem:
    """RAG system for comprehensive worldbuilding"""
    
    def __init__(self, storage_directory: Path):
        self.storage_directory = Path(storage_directory)
        self.worldbuilding_dir = self.storage_directory / "worldbuilding"
        self.worldbuilding_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Document storage
        self.documents: Dict[str, WorldbuildingDocument] = {}
        self.embedder = SimpleEmbedder()
        self.is_fitted = False
        
        # Category-specific storage for quick access
        self.docs_by_category: Dict[WorldbuildingCategory, List[str]] = {
            cat: [] for cat in WorldbuildingCategory
        }
        
        # Load existing worldbuilding data
        self._load_worldbuilding()
    
    def _load_worldbuilding(self):
        """Load worldbuilding documents from storage"""
        wb_file = self.worldbuilding_dir / "worldbuilding_database.json"
        
        if wb_file.exists():
            try:
                with open(wb_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for doc_data in data.get('documents', []):
                    doc = WorldbuildingDocument.from_dict(doc_data)
                    self.documents[doc.doc_id] = doc
                    self.docs_by_category[doc.category].append(doc.doc_id)

                removed = self.dedupe_documents(save=False)
                if removed:
                    self.logger.info(f"Removed {removed} duplicate worldbuilding documents")
                    self._save_worldbuilding()

                # Rebuild embeddings if we have documents
                if self.documents:
                    self._rebuild_embeddings()
                    
                self.logger.info(f"Loaded {len(self.documents)} worldbuilding documents")
            except Exception as e:
                self.logger.error(f"Error loading worldbuilding data: {e}")

    def _doc_key(self, *, title: str, category: WorldbuildingCategory) -> tuple[str, str]:
        return (str(getattr(category, 'value', str(category))), (title or '').strip().lower())

    def _find_doc_id_by_title_category(self, *, title: str, category: WorldbuildingCategory) -> Optional[str]:
        key = self._doc_key(title=title, category=category)
        for doc_id, doc in self.documents.items():
            try:
                if self._doc_key(title=doc.title, category=doc.category) == key:
                    return doc_id
            except Exception:
                continue
        return None

    def dedupe_documents(self, *, save: bool = True) -> int:
        """Remove duplicate docs by (category,title). Keeps the most recently updated doc."""
        if not self.documents:
            return 0

        buckets: Dict[tuple[str, str], List[str]] = {}
        for doc_id, doc in list(self.documents.items()):
            try:
                k = self._doc_key(title=doc.title, category=doc.category)
            except Exception:
                continue
            buckets.setdefault(k, []).append(doc_id)

        to_delete: List[str] = []
        for _, ids in buckets.items():
            if len(ids) <= 1:
                continue

            def _sort_key(did: str):
                d = self.documents.get(did)
                if not d:
                    return (datetime.min, datetime.min, did)
                return (getattr(d, 'updated_at', datetime.min), getattr(d, 'created_at', datetime.min), did)

            ids_sorted = sorted(ids, key=_sort_key, reverse=True)
            keep = ids_sorted[0]
            for did in ids_sorted[1:]:
                if did != keep:
                    to_delete.append(did)

        if not to_delete:
            # Also normalize category indexes just in case.
            self.docs_by_category = {cat: [] for cat in WorldbuildingCategory}
            for did, doc in self.documents.items():
                try:
                    self.docs_by_category[doc.category].append(did)
                except Exception:
                    pass
            return 0

        for did in to_delete:
            doc = self.documents.get(did)
            if not doc:
                continue
            try:
                if did in self.docs_by_category.get(doc.category, []):
                    self.docs_by_category[doc.category].remove(did)
            except Exception:
                pass
            try:
                del self.documents[did]
            except Exception:
                pass

        # Rebuild category index from scratch for consistency.
        self.docs_by_category = {cat: [] for cat in WorldbuildingCategory}
        for did, doc in self.documents.items():
            try:
                self.docs_by_category[doc.category].append(did)
            except Exception:
                pass

        if save:
            self._save_worldbuilding()

        return len(to_delete)
    
    def _save_worldbuilding(self):
        """Save worldbuilding documents to storage"""
        wb_file = self.worldbuilding_dir / "worldbuilding_database.json"
        
        try:
            data = {
                'documents': [doc.to_dict() for doc in self.documents.values()],
                'last_updated': datetime.now().isoformat(),
                'total_categories': len([cat for cat in WorldbuildingCategory if self.docs_by_category[cat]])
            }
            
            with open(wb_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Saved {len(self.documents)} worldbuilding documents")
        except Exception as e:
            self.logger.error(f"Error saving worldbuilding data: {e}")
    
    def _rebuild_embeddings(self):
        """Rebuild embeddings for all documents"""
        if not self.documents:
            return
        
        # Fit embedder on all documents
        texts = [doc.content for doc in self.documents.values()]
        self.embedder.fit(texts)
        self.is_fitted = True
        
        # Generate embeddings for each document
        for doc in self.documents.values():
            doc.embedding = self.embedder.embed(doc.content)
    
    def add_document(
        self,
        title: str,
        content: str,
        category: WorldbuildingCategory,
        subcategory: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance: int = 5,
        related_docs: Optional[List[str]] = None
    ) -> str:
        """Add a new worldbuilding document (upsert by category+title)."""
        existing_id = self._find_doc_id_by_title_category(title=title, category=category)
        if existing_id:
            self.update_document(
                existing_id,
                title=title,
                content=content,
                subcategory=subcategory,
                tags=tags,
                importance=importance,
                related_docs=related_docs,
            )
            return existing_id

        doc_id = f"{category.value}_{len(self.documents)}_{datetime.now().timestamp()}"
        
        doc = WorldbuildingDocument(
            doc_id=doc_id,
            title=title,
            content=content,
            category=category,
            subcategory=subcategory,
            tags=tags or [],
            importance=importance,
            related_docs=related_docs or []
        )
        
        self.documents[doc_id] = doc
        self.docs_by_category[category].append(doc_id)
        
        # Rebuild embeddings
        self._rebuild_embeddings()
        self._save_worldbuilding()
        
        self.logger.info(f"Added worldbuilding document: {title} [{category.value}]")
        return doc_id
    
    def update_document(
        self,
        doc_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        subcategory: Optional[str] = None,
        tags: Optional[List[str]] = None,
        importance: Optional[int] = None,
        related_docs: Optional[List[str]] = None
    ) -> bool:
        """Update an existing document"""
        if doc_id not in self.documents:
            self.logger.warning(f"Document {doc_id} not found")
            return False
        
        doc = self.documents[doc_id]
        
        if title is not None:
            doc.title = title
        if content is not None:
            doc.content = content
        if subcategory is not None:
            doc.subcategory = subcategory
        if tags is not None:
            doc.tags = tags
        if importance is not None:
            doc.importance = importance
        if related_docs is not None:
            doc.related_docs = related_docs
        
        doc.updated_at = datetime.now()
        
        # Rebuild embeddings if content changed
        if content is not None:
            self._rebuild_embeddings()
        
        self._save_worldbuilding()
        self.logger.info(f"Updated document: {doc.title}")
        return True
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id not in self.documents:
            return False
        
        doc = self.documents[doc_id]
        category = doc.category
        
        del self.documents[doc_id]
        if doc_id in self.docs_by_category[category]:
            self.docs_by_category[category].remove(doc_id)
        
        self._rebuild_embeddings()
        self._save_worldbuilding()
        
        self.logger.info(f"Deleted document: {doc.title}")
        return True
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[WorldbuildingCategory] = None,
        min_importance: int = 0,
        tags_filter: Optional[List[str]] = None
    ) -> List[Tuple[WorldbuildingDocument, float]]:
        """
        Search for relevant worldbuilding documents
        
        Returns list of (document, similarity_score) tuples
        """
        if not self.documents or not self.is_fitted:
            return []
        
        # Generate query embedding
        query_embedding = self.embedder.embed(query)
        
        # Calculate similarities
        results = []
        for doc in self.documents.values():
            # Apply filters
            if category_filter and doc.category != category_filter:
                continue
            if doc.importance < min_importance:
                continue
            if tags_filter and not any(tag in doc.tags for tag in tags_filter):
                continue
            
            # Calculate cosine similarity
            if doc.embedding is not None:
                similarity = np.dot(query_embedding, doc.embedding)
                results.append((doc, float(similarity)))
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results[:top_k]
    
    def get_by_category(
        self,
        category: WorldbuildingCategory,
        subcategory: Optional[str] = None
    ) -> List[WorldbuildingDocument]:
        """Get all documents in a category"""
        docs = [self.documents[doc_id] for doc_id in self.docs_by_category[category]]
        
        if subcategory:
            docs = [doc for doc in docs if doc.subcategory == subcategory]
        
        return docs
    
    def get_by_tags(self, tags: List[str]) -> List[WorldbuildingDocument]:
        """Get documents matching any of the given tags"""
        return [
            doc for doc in self.documents.values()
            if any(tag in doc.tags for tag in tags)
        ]
    
    def get_related_documents(self, doc_id: str, max_depth: int = 1) -> List[WorldbuildingDocument]:
        """Get related documents (recursive up to max_depth)"""
        if doc_id not in self.documents:
            return []
        
        related = []
        visited = set()
        to_visit = [(doc_id, 0)]
        
        while to_visit:
            current_id, depth = to_visit.pop(0)
            
            if current_id in visited or depth > max_depth:
                continue
            
            visited.add(current_id)
            
            if current_id in self.documents:
                doc = self.documents[current_id]
                if current_id != doc_id:
                    related.append(doc)
                
                if depth < max_depth:
                    for related_id in doc.related_docs:
                        if related_id not in visited:
                            to_visit.append((related_id, depth + 1))
        
        return related
    
    def get_context_for_llm(
        self,
        query: str,
        max_tokens: int = 1000,
        category_filter: Optional[WorldbuildingCategory] = None,
        include_related: bool = True
    ) -> str:
        """
        Get formatted worldbuilding context for LLM prompts
        
        Returns a formatted string with relevant worldbuilding information
        """
        trace_enabled = str(os.getenv('REALITAS_RAG_TRACE', '')).strip().lower() in ('1', 'true', 'yes', 'on')
        results = self.search(query, top_k=10, category_filter=category_filter)
        
        if not results:
            if trace_enabled:
                cf = category_filter.value if getattr(category_filter, 'value', None) else str(category_filter)
                self.logger.info(f"RAG_TRACE miss: category_filter={cf} query='{query}'")
            return ""
        
        context_parts = []
        current_tokens = 0
        included_docs = set()

        selected_doc_meta = []
        
        for doc, similarity in results:
            # Rough token estimation (4 chars per token)
            doc_tokens = len(doc.content) // 4
            remaining_tokens = max_tokens - current_tokens

            if remaining_tokens <= 0:
                break

            if doc_tokens > remaining_tokens:
                # Truncate to fit remaining budget rather than skip entirely.
                # Always include at least the first portion so callers get useful context.
                truncated_content = doc.content[:remaining_tokens * 4].rstrip()
                context_parts.append(f"\n**{doc.title}** [{get_category_display_name(doc.category)}] (excerpt):")
                if doc.subcategory:
                    context_parts.append(f"*Subcategory: {doc.subcategory}*")
                context_parts.append(f"{truncated_content}...\n")
                included_docs.add(doc.doc_id)
                current_tokens += remaining_tokens
            else:
                context_parts.append(f"\n**{doc.title}** [{get_category_display_name(doc.category)}]:")
                if doc.subcategory:
                    context_parts.append(f"*Subcategory: {doc.subcategory}*")
                context_parts.append(f"{doc.content}\n")
                included_docs.add(doc.doc_id)
                current_tokens += doc_tokens
            
            if trace_enabled:
                selected_doc_meta.append((doc.title, doc.category.value if hasattr(doc.category, 'value') else str(doc.category), float(similarity)))
            
            # Include related documents if requested and space available
            if include_related and current_tokens < max_tokens * 0.8:
                related = self.get_related_documents(doc.doc_id, max_depth=1)
                for related_doc in related:
                    if related_doc.doc_id in included_docs:
                        continue
                    
                    related_tokens = len(related_doc.content) // 4
                    if current_tokens + related_tokens > max_tokens:
                        break
                    
                    context_parts.append(f"\n  ↳ **Related: {related_doc.title}**")
                    context_parts.append(f"  {related_doc.content}\n")
                    
                    included_docs.add(related_doc.doc_id)
                    current_tokens += related_tokens

                    if trace_enabled:
                        selected_doc_meta.append((f"Related: {related_doc.title}", related_doc.category.value if hasattr(related_doc.category, 'value') else str(related_doc.category), None))

        combined = "\n".join(context_parts)

        if trace_enabled:
            cf = category_filter.value if getattr(category_filter, 'value', None) else str(category_filter)
            markers = []
            try:
                for cat in WorldbuildingCategory:
                    marker = f"SIMPLIFIED::{cat.value}"
                    if marker in combined:
                        markers.append(cat.value)
            except Exception:
                markers = []

            self.logger.info(
                f"RAG_TRACE hit: category_filter={cf} query='{query}' "
                f"docs={len(selected_doc_meta)} markers={markers}"
            )
            if selected_doc_meta:
                for title, cat_value, sim in selected_doc_meta[:20]:
                    self.logger.info(f"RAG_TRACE doc: [{cat_value}] {title} sim={sim}")

        return combined
    
    def query(
        self,
        query_text: str,
        top_k: int = 5,
        max_tokens: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Query the RAG system for relevant worldbuilding context.
        This is an alias/wrapper for search() that returns a simpler format.
        
        Args:
            query_text: The search query
            top_k: Maximum number of results
            max_tokens: Maximum tokens to return (approximate)
            
        Returns:
            List of dicts with 'content', 'title', 'category', 'similarity' keys
        """
        results = self.search(query_text, top_k=top_k)
        
        output = []
        current_tokens = 0
        
        for doc, similarity in results:
            doc_tokens = len(doc.content) // 4
            if current_tokens + doc_tokens > max_tokens:
                break
                
            output.append({
                'content': doc.content,
                'title': doc.title,
                'category': doc.category.value if hasattr(doc.category, 'value') else str(doc.category),
                'similarity': similarity
            })
            current_tokens += doc_tokens
        
        return output
    
    def get_category_summary(self) -> Dict[str, int]:
        """Get summary of documents per category"""
        return {
            get_category_display_name(cat): len(doc_ids)
            for cat, doc_ids in self.docs_by_category.items()
            if doc_ids
        }
    
    def clear_all(self):
        """Clear all documents"""
        self.documents.clear()
        self.docs_by_category = {cat: [] for cat in WorldbuildingCategory}
        self.is_fitted = False
        self._save_worldbuilding()


# ============================================================================
# GLOBAL INSTANCE MANAGEMENT
# ============================================================================

_worldbuilding_rag: Optional[WorldbuildingRAGSystem] = None


def initialize_worldbuilding_rag(storage_directory: Path) -> WorldbuildingRAGSystem:
    """Initialize the global worldbuilding RAG system"""
    global _worldbuilding_rag
    _worldbuilding_rag = WorldbuildingRAGSystem(storage_directory)
    return _worldbuilding_rag


def get_worldbuilding_rag() -> WorldbuildingRAGSystem:
    """Get the global worldbuilding RAG system instance"""
    if _worldbuilding_rag is None:
        raise RuntimeError("Worldbuilding RAG system not initialized. Call initialize_worldbuilding_rag() first.")
    return _worldbuilding_rag
