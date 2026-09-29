"use client";

import {
  ChangeEvent,
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import Link from "next/link";
import { useParams } from "next/navigation";

import type {
  KnowledgeJob,
  Material,
  MaterialChunk,
  SearchResult,
} from "@/lib/eduagent-api";

import {
  getKnowledgeJob,
  listChunks,
  listMaterials,
  processMaterial,
  searchKnowledge,
  uploadMaterial,
} from "@/lib/eduagent-api";


/* =========================================================
 * Generic helpers
 * ========================================================= */

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}


function getErrorMessage(
  error: unknown,
  fallback = "Unknown error"
): string {
  return error instanceof Error
    ? error.message
    : fallback;
}


/**
 * Accept both real numbers and numeric strings.
 *
 * API contracts should eventually guarantee numbers,
 * but this debug UI should never crash because a backend
 * field is null / undefined / "0.82".
 */
function toFiniteNumber(
  value: unknown
): number | null {
  if (
    typeof value === "number" &&
    Number.isFinite(value)
  ) {
    return value;
  }

  if (
    typeof value === "string" &&
    value.trim() !== ""
  ) {
    const parsed = Number(value);

    if (Number.isFinite(parsed)) {
      return parsed;
    }
  }

  return null;
}


function firstFiniteNumber(
  ...values: unknown[]
): number | null {
  for (const value of values) {
    const number =
      toFiniteNumber(value);

    if (number !== null) {
      return number;
    }
  }

  return null;
}


function formatNumber(
  value: unknown,
  digits = 4
): string {
  const number =
    toFiniteNumber(value);

  return number === null
    ? "—"
    : number.toFixed(digits);
}


function formatRank(
  value: unknown
): string {
  const number =
    toFiniteNumber(value);

  if (number !== null) {
    return String(
      Math.trunc(number)
    );
  }

  if (
    typeof value === "string" &&
    value.trim() !== ""
  ) {
    return value;
  }

  return "—";
}


function normalizeProgress(
  value: unknown
): number {
  const number =
    toFiniteNumber(value);

  if (number === null) {
    return 0;
  }

  return Math.max(
    0,
    Math.min(100, number)
  );
}


function displayText(
  value: unknown,
  fallback = "—"
): string {
  if (
    typeof value === "string" &&
    value.trim() !== ""
  ) {
    return value;
  }

  return fallback;
}


/* =========================================================
 * Component
 * ========================================================= */

export default function MaterialsPage() {
  const params = useParams<{
    courseId: string;
  }>();

  const courseId =
    params.courseId;


  /* -------------------------------------------------------
   * Materials
   * ------------------------------------------------------- */

  const [
    materials,
    setMaterials,
  ] = useState<Material[]>([]);

  const [
    jobs,
    setJobs,
  ] = useState<
    Record<string, KnowledgeJob>
  >({});

  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(null);

  const [
    uploading,
    setUploading,
  ] = useState(false);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );


  /* -------------------------------------------------------
   * Chunk preview
   * ------------------------------------------------------- */

  const [
    selectedMaterial,
    setSelectedMaterial,
  ] = useState<Material | null>(
    null
  );

  const [
    chunks,
    setChunks,
  ] = useState<MaterialChunk[]>([]);

  const [
    loadingChunks,
    setLoadingChunks,
  ] = useState(false);


  /* -------------------------------------------------------
   * Retrieval
   * ------------------------------------------------------- */

  const [
    query,
    setQuery,
  ] = useState("");

  const [
    searching,
    setSearching,
  ] = useState(false);

  const [
    results,
    setResults,
  ] = useState<SearchResult[]>([]);


  /* =======================================================
   * Material loading
   * ======================================================= */

  const loadMaterials =
    useCallback(
      async () => {
        setLoading(true);
        setError(null);

        try {
          const data =
            await listMaterials(
              courseId
            );

          if (!Array.isArray(data)) {
            throw new Error(
              "Invalid materials response: expected an array."
            );
          }

          setMaterials(data);
        } catch (err) {
          setError(
            getErrorMessage(
              err,
              "Failed to load materials"
            )
          );
        } finally {
          setLoading(false);
        }
      },
      [courseId]
    );


  /*
   * Initial load.
   *
   * Do not call loadMaterials() here because that function
   * performs synchronous setState before awaiting.
   * This avoids react-hooks/set-state-in-effect.
   */
  useEffect(() => {
    const controller =
      new AbortController();

    void listMaterials(
      courseId,
      controller.signal
    )
      .then((data) => {
        if (
          controller.signal.aborted
        ) {
          return;
        }

        if (!Array.isArray(data)) {
          throw new Error(
            "Invalid materials response: expected an array."
          );
        }

        setMaterials(data);
      })
      .catch((err) => {
        if (
          controller.signal.aborted
        ) {
          return;
        }

        setError(
          getErrorMessage(
            err,
            "Failed to load materials"
          )
        );
      })
      .finally(() => {
        if (
          !controller.signal.aborted
        ) {
          setLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [courseId]);


  /* =======================================================
   * Upload
   * ======================================================= */

  async function handleUpload(
    event:
      FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!selectedFile) {
      return;
    }

    setUploading(true);
    setError(null);

    try {
      await uploadMaterial(
        courseId,
        selectedFile
      );

      setSelectedFile(null);

      /*
       * Reset the native file input visually.
       * React state alone does not clear browser file input.
       */
      const form =
        event.currentTarget;

      form.reset();

      await loadMaterials();
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Upload failed"
        )
      );
    } finally {
      setUploading(false);
    }
  }


  function handleFileChange(
    event:
      ChangeEvent<HTMLInputElement>
  ) {
    const file =
      event.target.files?.[0];

    setSelectedFile(
      file ?? null
    );
  }


  /* =======================================================
   * Processing jobs
   * ======================================================= */

  async function pollJob(
    materialId: string,
    jobId: string
  ) {
    if (
      typeof jobId !== "string" ||
      jobId.trim() === ""
    ) {
      throw new Error(
        "Cannot poll knowledge job: missing job id."
      );
    }

    for (
      let iteration = 0;
      iteration < 240;
      iteration += 1
    ) {
      const job =
        await getKnowledgeJob(
          jobId
        );

      /*
       * Runtime API guard.
       *
       * TypeScript types do not validate JSON received from
       * the backend at runtime.
       */
      if (
        !job ||
        typeof job !== "object" ||
        typeof job.status !== "string"
      ) {
        throw new Error(
          "Invalid knowledge job response."
        );
      }

      setJobs((current) => ({
        ...current,
        [materialId]: job,
      }));

      const terminal =
        job.status === "succeeded" ||
        job.status === "failed" ||
        job.status === "cancelled";

      if (terminal) {
        await loadMaterials();

        return;
      }

      await sleep(1500);
    }

    throw new Error(
      "Processing job polling timed out."
    );
  }


  async function handleProcess(
    material: Material
  ) {
    setError(null);

    try {
      const job =
        await processMaterial(
          material.id
        );

      if (
        !job ||
        typeof job !== "object" ||
        typeof job.id !== "string" ||
        job.id.trim() === "" ||
        typeof job.status !== "string"
      ) {
        throw new Error(
          "Invalid processing job response: backend did not return a valid KnowledgeJob."
        );
      }

      setJobs((current) => ({
        ...current,
        [material.id]: job,
      }));

      await pollJob(
        material.id,
        job.id
      );
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Processing failed"
        )
      );
    }
  }


  /* =======================================================
   * Chunk preview
   * ======================================================= */

  async function handleViewChunks(
    material: Material
  ) {
    setSelectedMaterial(
      material
    );

    setLoadingChunks(true);
    setChunks([]);
    setError(null);

    try {
      const data =
        await listChunks(
          material.id
        );

      if (!Array.isArray(data)) {
        throw new Error(
          "Invalid chunks response: expected an array."
        );
      }

      setChunks(data);
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Failed to load chunks"
        )
      );
    } finally {
      setLoadingChunks(false);
    }
  }


  /* =======================================================
   * Search / retrieval
   * ======================================================= */

  async function handleSearch(
    event:
      FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    const trimmedQuery =
      query.trim();

    if (!trimmedQuery) {
      return;
    }

    setSearching(true);
    setResults([]);
    setError(null);

    try {
      const data =
        await searchKnowledge(
          courseId,
          trimmedQuery,
          5
        );

      /*
       * Again: API JSON is runtime data.
       * Never trust TypeScript alone.
       */
      if (!Array.isArray(data)) {
        throw new Error(
          "Invalid knowledge search response: expected an array."
        );
      }

      setResults(data);
    } catch (err) {
      setError(
        getErrorMessage(
          err,
          "Search failed"
        )
      );
    } finally {
      setSearching(false);
    }
  }


  /* =======================================================
   * Render
   * ======================================================= */

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-10 text-zinc-950">
      <div className="mx-auto max-w-6xl space-y-10">

        {/* =================================================
         * Header
         * ================================================= */}

        <header>
          <Link
            href="/"
            className="text-sm text-zinc-500 hover:text-zinc-950"
          >
            ← Courses
          </Link>

          <p className="mt-6 text-sm font-medium text-zinc-500">
            EduAgent · Teacher Workbench
          </p>

          <h1 className="mt-2 text-4xl font-semibold tracking-tight">
            Material Workspace
          </h1>

          <p className="mt-3 break-all text-sm text-zinc-500">
            Course: {courseId}
          </p>
        </header>


        {/* =================================================
         * Global error
         * ================================================= */}

        {error && (
          <div
            role="alert"
            className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700"
          >
            {error}
          </div>
        )}


        {/* =================================================
         * Upload
         * ================================================= */}

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">
            Upload Material
          </h2>

          <p className="mt-2 text-sm text-zinc-500">
            PDF, PPTX, DOCX, TXT or Markdown.
          </p>

          <form
            onSubmit={handleUpload}
            className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center"
          >
            <input
              type="file"
              accept=".pdf,.pptx,.docx,.txt,.md,.markdown"
              onChange={
                handleFileChange
              }
              disabled={uploading}
              className="block w-full rounded-lg border border-zinc-300 bg-white p-3 disabled:opacity-50"
            />

            <button
              type="submit"
              disabled={
                uploading ||
                !selectedFile
              }
              className="shrink-0 rounded-lg bg-zinc-950 px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {uploading
                ? "Uploading..."
                : "Upload"}
            </button>
          </form>
        </section>


        {/* =================================================
         * Materials
         * ================================================= */}

        <section>
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold">
              Course Materials
            </h2>

            <button
              type="button"
              onClick={() => {
                void loadMaterials();
              }}
              disabled={loading}
              className="text-sm font-medium text-zinc-600 hover:text-zinc-950 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading
                ? "Refreshing..."
                : "Refresh"}
            </button>
          </div>

          {loading ? (
            <p className="mt-5 text-zinc-500">
              Loading materials...
            </p>
          ) : materials.length === 0 ? (
            <div className="mt-5 rounded-xl border border-dashed border-zinc-300 p-10 text-center text-zinc-500">
              No course materials yet.
            </div>
          ) : (
            <div className="mt-5 space-y-4">
              {materials.map(
                (material) => {
                  const job =
                    jobs[
                      material.id
                    ];

                  const active =
                    job?.status ===
                      "queued" ||
                    job?.status ===
                      "processing";

                  const progress =
                    normalizeProgress(
                      job?.progress
                    );

                  return (
                    <article
                      key={material.id}
                      className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
                    >
                      <div className="flex flex-col justify-between gap-4 md:flex-row">

                        <div className="min-w-0">
                          <h3 className="break-words text-lg font-semibold">
                            {displayText(
                              material.original_filename,
                              "Unnamed material"
                            )}
                          </h3>

                          <div className="mt-2 flex flex-wrap gap-2 text-xs">
                            <span className="rounded-full bg-zinc-100 px-3 py-1">
                              {displayText(
                                material.source_type
                              )}
                            </span>

                            <span className="rounded-full bg-zinc-100 px-3 py-1">
                              {displayText(
                                material.status
                              )}
                            </span>
                          </div>


                          {job && (
                            <div className="mt-4">
                              <p className="text-sm text-zinc-600">
                                Job:{" "}
                                {displayText(
                                  job.status
                                )}
                                {" · "}
                                {displayText(
                                  job.stage
                                )}
                                {" · "}
                                {formatNumber(
                                  progress,
                                  0
                                )}
                                %
                              </p>

                              <div className="mt-2 h-2 w-full max-w-md overflow-hidden rounded-full bg-zinc-100">
                                <div
                                  className="h-full bg-zinc-900 transition-all"
                                  style={{
                                    width:
                                      `${progress}%`,
                                  }}
                                />
                              </div>

                              {job.error_json && (
                                <pre className="mt-3 max-w-2xl overflow-auto rounded-lg bg-red-50 p-3 text-xs text-red-700">
                                  {JSON.stringify(
                                    job.error_json,
                                    null,
                                    2
                                  )}
                                </pre>
                              )}
                            </div>
                          )}
                        </div>


                        <div className="flex shrink-0 flex-wrap items-start gap-2">

                          {material.status !==
                            "ready" &&
                            !active && (
                              <button
                                type="button"
                                onClick={() => {
                                  void handleProcess(
                                    material
                                  );
                                }}
                                className="rounded-lg bg-zinc-950 px-4 py-2 text-sm font-medium text-white"
                              >
                                {material.status ===
                                "failed"
                                  ? "Retry"
                                  : "Process"}
                              </button>
                            )}


                          {active && (
                            <button
                              type="button"
                              disabled
                              className="rounded-lg bg-zinc-200 px-4 py-2 text-sm font-medium text-zinc-500"
                            >
                              Processing...
                            </button>
                          )}


                          {material.status ===
                            "ready" && (
                              <button
                                type="button"
                                onClick={() => {
                                  void handleViewChunks(
                                    material
                                  );
                                }}
                                className="rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium hover:bg-zinc-50"
                              >
                                View Chunks
                              </button>
                            )}
                        </div>
                      </div>
                    </article>
                  );
                }
              )}
            </div>
          )}
        </section>


        {/* =================================================
         * Chunk / Evidence Preview
         * ================================================= */}

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">
            Chunk / Evidence Preview
          </h2>

          {!selectedMaterial ? (
            <p className="mt-4 text-sm text-zinc-500">
              Select a ready material.
            </p>
          ) : (
            <>
              <p className="mt-3 text-sm text-zinc-500">
                {displayText(
                  selectedMaterial.original_filename,
                  "Unnamed material"
                )}
              </p>

              {loadingChunks ? (
                <p className="mt-5 text-zinc-500">
                  Loading chunks...
                </p>
              ) : chunks.length === 0 ? (
                <p className="mt-5 text-sm text-zinc-500">
                  No chunks found.
                </p>
              ) : (
                <div className="mt-5 max-h-[560px] space-y-4 overflow-auto">
                  {chunks.map(
                    (
                      chunk,
                      index
                    ) => (
                      <article
                        key={
                          chunk.id ??
                          `${selectedMaterial.id}-${index}`
                        }
                        className="rounded-xl border border-zinc-200 p-4"
                      >
                        <div className="flex flex-wrap gap-2 text-xs text-zinc-500">
                          <span>
                            Chunk #{" "}
                            {formatRank(
                              chunk.chunk_index
                            )}
                          </span>

                          <span>
                            Page:{" "}
                            {chunk.page_no ??
                              "—"}
                          </span>

                          <span>
                            Tokens≈{" "}
                            {formatRank(
                              chunk.token_count
                            )}
                          </span>
                        </div>

                        <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-zinc-700">
                          {displayText(
                            chunk.text,
                            "No chunk text."
                          )}
                        </p>
                      </article>
                    )
                  )}
                </div>
              )}
            </>
          )}
        </section>


        {/* =================================================
         * Retrieval + Rerank
         * ================================================= */}

        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">
            Retrieval + Rerank Debug
          </h2>

          <p className="mt-2 text-sm text-zinc-500">
            Inspect vector retrieval and reranker
            outputs without assuming every optional
            score is present.
          </p>

          <form
            onSubmit={handleSearch}
            className="mt-5 flex flex-col gap-3 md:flex-row"
          >
            <input
              value={query}
              onChange={(event) => {
                setQuery(
                  event.target.value
                );
              }}
              placeholder="Ask a question about course materials..."
              className="flex-1 rounded-lg border border-zinc-300 px-4 py-3"
            />

            <button
              type="submit"
              disabled={
                searching ||
                !query.trim()
              }
              className="rounded-lg bg-zinc-950 px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {searching
                ? "Searching..."
                : "Search"}
            </button>
          </form>


          {searching && (
            <p className="mt-6 text-sm text-zinc-500">
              Searching...
            </p>
          )}


          {!searching &&
            results.length === 0 && (
              <p className="mt-6 text-sm text-zinc-500">
                No search results yet.
              </p>
            )}


          <div className="mt-6 space-y-4">
            {results.map(
              (
                result,
                index
              ) => {
                /*
                 * During the M2 transition some backend
                 * responses provide similarity but not
                 * retrieval_score yet.
                 *
                 * Prefer explicit retrieval_score.
                 * similarity is only a compatibility
                 * fallback.
                 */
                const vectorScore =
                  firstFiniteNumber(
                    result.retrieval_score,
                    result.similarity
                  );

                return (
                  <article
                    key={
                      result.chunk_id ??
                      result.evidence_id ??
                      `search-result-${index}`
                    }
                    className="rounded-xl border border-zinc-200 p-5"
                  >
                    <div className="flex flex-wrap gap-3 text-xs text-zinc-500">

                      <strong>
                        Result #
                        {index + 1}
                      </strong>


                      <span>
                        Page{" "}
                        {result.page_no ??
                          "—"}
                      </span>


                      <span>
                        Vector rank{" "}
                        {formatRank(
                          result.retrieval_rank
                        )}
                      </span>


                      <span>
                        Vector score{" "}
                        {formatNumber(
                          vectorScore
                        )}
                      </span>


                      <span>
                        Similarity{" "}
                        {formatNumber(
                          result.similarity
                        )}
                      </span>


                      <span>
                        Distance{" "}
                        {formatNumber(
                          result.distance
                        )}
                      </span>


                      <span>
                        Rerank rank{" "}
                        {formatRank(
                          result.rerank_rank
                        )}
                      </span>


                      <span>
                        Rerank score{" "}
                        {formatNumber(
                          result.rerank_score
                        )}
                      </span>
                    </div>


                    <p className="mt-4 whitespace-pre-wrap text-sm leading-6 text-zinc-700">
                      {displayText(
                        result.text,
                        "No result text."
                      )}
                    </p>


                    <p className="mt-3 break-all text-xs text-zinc-400">
                      Evidence:{" "}
                      {displayText(
                        result.evidence_id
                      )}
                    </p>


                    <p className="mt-1 break-all text-xs text-zinc-400">
                      Chunk:{" "}
                      {displayText(
                        result.chunk_id
                      )}
                    </p>
                  </article>
                );
              }
            )}
          </div>
        </section>

      </div>
    </main>
  );
}