export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

export const DEV_USER_ID =
  process.env.NEXT_PUBLIC_DEV_USER_ID ??
  "00000000-0000-0000-0000-000000000001";


export type Material = {
  id: string;
  owner_id: string;
  course_id: string;
  asset_id: string;

  source_type: string;
  original_filename: string;

  status:
    | "uploaded"
    | "processing"
    | "ready"
    | "failed"
    | string;

  created_at: string;
  updated_at: string;
};


export type KnowledgeJob = {
  id: string;
  material_id: string;
  owner_id: string;

  job_type: string;

  status:
    | "queued"
    | "processing"
    | "succeeded"
    | "failed"
    | "cancelled"
    | string;

  stage: string;
  progress: number;

  attempt: number;
  max_attempts: number;

  trace_id: string | null;

  error_json: Record<string, unknown> | null;
  result_json: Record<string, unknown> | null;

  created_at: string;
  updated_at: string;

  started_at: string | null;
  finished_at: string | null;
};


export type MaterialChunk = {
  id: string;
  material_id: string;

  chunk_index: number;

  page_no: number | null;
  section: string | null;

  text: string;
  token_count: number;
};


export type SearchResult = {
  chunk_id: string;
  material_id: string;
  evidence_id: string;

  text: string;

  page_no: number | null;
  section: string | null;

  distance: number;
  similarity: number;

  retrieval_rank: number | null;
  retrieval_score: number | null;

  rerank_rank: number | null;
  rerank_score: number | null;

  locator: Record<string, unknown>;
};


async function readError(
  response: Response
): Promise<string> {
  const body = await response.text();

  return body || response.statusText;
}


function baseHeaders(): Headers {
  const headers = new Headers();

  headers.set(
    "X-User-Id",
    DEV_USER_ID
  );

  return headers;
}


export async function listMaterials(
  courseId: string,
  signal?: AbortSignal
): Promise<Material[]> {
  const response = await fetch(
    `${API_BASE_URL}/materials?course_id=${encodeURIComponent(
      courseId
    )}`,
    {
      cache: "no-store",
      headers: baseHeaders(),
      signal,
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to load materials: ${
        response.status
      } ${await readError(response)}`
    );
  }

  return response.json();
}


export async function uploadMaterial(
  courseId: string,
  file: File
): Promise<Material> {
  const body = new FormData();

  body.append(
    "course_id",
    courseId
  );

  body.append(
    "file",
    file
  );

  const response = await fetch(
    `${API_BASE_URL}/materials`,
    {
      method: "POST",
      headers: baseHeaders(),
      body,
    }
  );

  if (!response.ok) {
    throw new Error(
      `Upload failed: ${
        response.status
      } ${await readError(response)}`
    );
  }

  return response.json();
}


export async function processMaterial(
  materialId: string
): Promise<KnowledgeJob> {
  const response = await fetch(
    `${API_BASE_URL}/materials/${materialId}/process`,
    {
      method: "POST",
      headers: baseHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(
      `Process failed: ${
        response.status
      } ${await readError(response)}`
    );
  }

  const data =
    await response.json();

  if (
    typeof data.id !== "string" ||
    typeof data.material_id !== "string" ||
    typeof data.status !== "string"
  ) {
    throw new Error(
      "Backend is still using the synchronous " +
      "/process contract. Expected KnowledgeJob, got: " +
      JSON.stringify(data)
    );
  }

  return data;

}


export async function getKnowledgeJob(
  jobId: string
): Promise<KnowledgeJob> {
  const response = await fetch(
    `${API_BASE_URL}/knowledge/jobs/${jobId}`,
    {
      cache: "no-store",
      headers: baseHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(
      `Job lookup failed: ${
        response.status
      } ${await readError(response)}`
    );
  }

  return response.json();
}


export async function listChunks(
  materialId: string
): Promise<MaterialChunk[]> {
  const response = await fetch(
    `${API_BASE_URL}/materials/${materialId}/chunks`,
    {
      cache: "no-store",
      headers: baseHeaders(),
    }
  );

  if (!response.ok) {
    throw new Error(
      `Chunk lookup failed: ${
        response.status
      } ${await readError(response)}`
    );
  }

  return response.json();
}


export async function searchKnowledge(
  courseId: string,
  query: string,
  topK = 5
): Promise<SearchResult[]> {
  const headers = baseHeaders();

  headers.set(
    "Content-Type",
    "application/json"
  );

  const response = await fetch(
    `${API_BASE_URL}/knowledge/search`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({
        course_id: courseId,
        query,
        top_k: topK,
      }),
    }
  );

  if (!response.ok) {
    throw new Error(
      `Knowledge search failed: ${
        response.status
      } ${await readError(response)}`
    );
  }

  return response.json();
}
