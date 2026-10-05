from typing import Sequence

from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.schema import BaseNode


class DeleteSafeIngestionPipeline(IngestionPipeline):
    """Upsert documents and drop stored nodes that are no longer in the source set.

    LlamaIndex 0.14 deletes by document-hash values, which misses chunk nodes
    whose ids differ from the source document id. This override deletes those
    orphan nodes before the parent pipeline writes the surviving documents.
    """

    def _handle_upserts(self, nodes: Sequence[BaseNode]) -> Sequence[BaseNode]:
        assert self.docstore is not None

        doc_ids_from_nodes = set()
        nodes_to_run = []
        for node in nodes:
            ref_doc_id = node.ref_doc_id if node.ref_doc_id else node.id_
            doc_ids_from_nodes.add(ref_doc_id)
            existing_hash = self.docstore.get_document_hash(ref_doc_id)
            if not existing_hash:
                nodes_to_run.append(node)
            elif existing_hash != node.hash:
                self.docstore.delete_ref_doc(ref_doc_id, raise_error=False)
                if self.vector_store is not None:
                    self.vector_store.delete(ref_doc_id)
                nodes_to_run.append(node)

        if self.docstore_strategy == DocstoreStrategy.UPSERTS_AND_DELETE:
            self._delete_missing_documents(nodes, doc_ids_from_nodes)

        return nodes_to_run

    async def _ahandle_upserts(
            self,
            nodes: Sequence[BaseNode],
            store_doc_text: bool = True,
    ) -> Sequence[BaseNode]:
        assert self.docstore is not None

        doc_ids_from_nodes = set()
        nodes_to_run = []
        for node in nodes:
            ref_doc_id = node.ref_doc_id if node.ref_doc_id else node.id_
            doc_ids_from_nodes.add(ref_doc_id)
            existing_hash = await self.docstore.aget_document_hash(ref_doc_id)
            if not existing_hash:
                nodes_to_run.append(node)
            elif existing_hash != node.hash:
                await self.docstore.adelete_ref_doc(ref_doc_id, raise_error=False)
                if self.vector_store is not None:
                    await self.vector_store.adelete(ref_doc_id)
                nodes_to_run.append(node)

        if self.docstore_strategy == DocstoreStrategy.UPSERTS_AND_DELETE:
            await self._adelete_missing_documents(nodes, doc_ids_from_nodes)

        return nodes_to_run

    def _delete_missing_documents(self, nodes, doc_ids_from_nodes):
        for ref_doc_id in self._missing_document_ids(nodes, doc_ids_from_nodes):
            self.docstore.delete_document(ref_doc_id, raise_error=False)
            if self.vector_store is not None:
                self.vector_store.delete(ref_doc_id)

    async def _adelete_missing_documents(self, nodes, doc_ids_from_nodes):
        for ref_doc_id in self._missing_document_ids(nodes, doc_ids_from_nodes):
            await self.docstore.adelete_document(ref_doc_id, raise_error=False)
            if self.vector_store is not None:
                await self.vector_store.adelete(ref_doc_id)

    def _missing_document_ids(self, nodes, doc_ids_from_nodes):
        passed_hashes = {node.hash for node in nodes}
        stored_docs = self.docstore.docs
        missing_ids = set()
        for doc in stored_docs.values():
            parent = stored_docs.get(doc.ref_doc_id) if doc.ref_doc_id else None
            kept_by_parent = (
                doc.ref_doc_id in doc_ids_from_nodes
                and parent is not None
                and parent.hash in passed_hashes
            )
            if doc.id_ in doc_ids_from_nodes or kept_by_parent:
                continue
            missing_ids.add(doc.id_)
        return missing_ids
