import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export interface Document {
  id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  asset_id: string | null;
  uploaded_at: string;
}

export function useDocuments() {
  return useQuery<Document[]>({
    queryKey: ["documents"],
    queryFn: () => api.get("/documents"),
    staleTime: 30_000,
  });
}

export function useAssetDocuments(assetId: string) {
  return useQuery<Document[]>({
    queryKey: ["documents", "asset", assetId],
    queryFn: () => api.get(`/documents/asset/${assetId}`),
    staleTime: 30_000,
    enabled: !!assetId,
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ file, assetId }: { file: File; assetId?: string }) => {
      const path = assetId ? `/documents/upload?asset_id=${assetId}` : "/documents/upload";
      return api.upload<Document>(path, file);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/documents/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents"] });
    },
  });
}
