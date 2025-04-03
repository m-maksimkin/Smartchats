from typing import Any, Generator, List, Optional, Sequence, Union

from llama_index.core.ingestion import DocstoreStrategy, IngestionPipeline
from llama_index.core.schema import (BaseNode, Document, MetadataMode,
                                     TransformComponent)


class DeleteSafeIngestionPipeline(IngestionPipeline):

    def _handle_upserts(
            self,
            nodes: Sequence[BaseNode],
            store_doc_text: bool = True,
    ) -> Sequence[BaseNode]:
        """Handle docstore upserts by checking hashes and ids."""
        assert self.docstore is not None

        doc_ids_from_nodes = set()
        deduped_nodes_to_run = {}
        for node in nodes:
            ref_doc_id = node.ref_doc_id if node.ref_doc_id else node.id_
            doc_ids_from_nodes.add(ref_doc_id)
            existing_hash = self.docstore.get_document_hash(ref_doc_id)
            if not existing_hash:
                # document doesn't exist, so add it
                deduped_nodes_to_run[ref_doc_id] = node
            elif existing_hash and existing_hash != node.hash:
                self.docstore.delete_ref_doc(ref_doc_id, raise_error=False)

                if self.vector_store is not None:
                    self.vector_store.delete(ref_doc_id)

                deduped_nodes_to_run[ref_doc_id] = node
            else:
                continue  # document exists and is unchanged, so skip it

        if self.docstore_strategy == DocstoreStrategy.UPSERTS_AND_DELETE:
            # Identify missing docs and delete them from docstore and vector store
            doc_ids_to_delete = set()
            passed_nodes_hashes = set([node.hash for node in nodes])
            for doc in self.docstore.docs.values():
                if (doc.id_ in doc_ids_from_nodes
                        or doc.ref_doc_id in doc_ids_from_nodes
                        and self.docstore.docs.get(doc.ref_doc_id).hash in passed_nodes_hashes):
                    continue
                doc_ids_to_delete.add(doc.id_)
            for ref_doc_id in doc_ids_to_delete:
                self.docstore.delete_document(ref_doc_id)

                if self.vector_store is not None:
                    self.vector_store.delete(ref_doc_id)

        nodes_to_run = list(deduped_nodes_to_run.values())
        self.docstore.set_document_hashes({n.id_: n.hash for n in nodes_to_run})
        self.docstore.add_documents(nodes_to_run, store_text=store_doc_text)

        return nodes_to_run

    async def _ahandle_upserts(
            self,
            nodes: Sequence[BaseNode],
            store_doc_text: bool = True,
    ) -> Sequence[BaseNode]:
        """Handle docstore upserts by checking hashes and ids."""
        assert self.docstore is not None

        doc_ids_from_nodes = set()
        deduped_nodes_to_run = {}
        for node in nodes:
            ref_doc_id = node.ref_doc_id if node.ref_doc_id else node.id_
            doc_ids_from_nodes.add(ref_doc_id)
            existing_hash = await self.docstore.aget_document_hash(ref_doc_id)
            if not existing_hash:
                # document doesn't exist, so add it
                deduped_nodes_to_run[ref_doc_id] = node
            elif existing_hash and existing_hash != node.hash:
                await self.docstore.adelete_ref_doc(ref_doc_id, raise_error=False)

                if self.vector_store is not None:
                    await self.vector_store.adelete(ref_doc_id)

                deduped_nodes_to_run[ref_doc_id] = node
            else:
                continue  # document exists and is unchanged, so skip it

        if self.docstore_strategy == DocstoreStrategy.UPSERTS_AND_DELETE:
            # Identify missing docs and delete them from docstore and vector store
            doc_ids_to_delete = set()
            passed_nodes_hashes = set([node.hash for node in nodes])
            for doc in self.docstore.docs.values():
                if (doc.id_ in doc_ids_from_nodes
                        or doc.ref_doc_id in doc_ids_from_nodes
                        and self.docstore.docs.get(doc.ref_doc_id).hash in passed_nodes_hashes):
                    continue
                doc_ids_to_delete.add(doc.id_)

            for ref_doc_id in doc_ids_to_delete:
                await self.docstore.adelete_document(ref_doc_id)

                if self.vector_store is not None:
                    await self.vector_store.adelete(ref_doc_id)

        nodes_to_run = list(deduped_nodes_to_run.values())
        await self.docstore.async_add_documents(nodes_to_run, store_text=store_doc_text)
        await self.docstore.aset_document_hashes({n.id_: n.hash for n in nodes_to_run})

        return nodes_to_run
