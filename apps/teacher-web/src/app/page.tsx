"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";


type Course = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  current_version_id: string | null;
  version_no: number | null;
  version_state: string | null;
  created_at: string;
  updated_at: string;
};


const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  "http://localhost:8000";

const DEV_USER_ID =
  process.env.NEXT_PUBLIC_DEV_USER_ID ??
  "00000000-0000-0000-0000-000000000001";


export default function Home() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);


  const loadCourses = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/courses`,
        {
          headers: {
            "X-User-Id": DEV_USER_ID,
          },
        }
      );

      if (!response.ok) {
        throw new Error(
          `Failed to load courses: ${response.status}`
        );
      }

      const data = await response.json();

      setCourses(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unknown error"
      );
    } finally {
      setLoading(false);
    }
  }, []);


  useEffect(() => {
    loadCourses();
  }, [loadCourses]);


  async function createCourse(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    if (!title.trim()) {
      return;
    }

    setCreating(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/courses`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-User-Id": DEV_USER_ID,
          },
          body: JSON.stringify({
            title: title.trim(),
            description:
              description.trim() || null,
          }),
        }
      );

      if (!response.ok) {
        const body = await response.text();

        throw new Error(
          `Failed to create course: ${response.status} ${body}`
        );
      }

      setTitle("");
      setDescription("");

      await loadCourses();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unknown error"
      );
    } finally {
      setCreating(false);
    }
  }


  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-12 text-zinc-950">
      <div className="mx-auto max-w-5xl space-y-10">

        <header>
          <p className="text-sm font-medium text-zinc-500">
            EduAgent · Teacher Workbench
          </p>

          <h1 className="mt-2 text-4xl font-semibold tracking-tight">
            Courses
          </h1>

          <p className="mt-3 text-zinc-600">
            Create and manage versioned AI courses.
          </p>
        </header>


        <section className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold">
            Create course
          </h2>

          <form
            className="mt-6 space-y-4"
            onSubmit={createCourse}
          >
            <div>
              <label className="mb-2 block text-sm font-medium">
                Title
              </label>

              <input
                className="w-full rounded-lg border border-zinc-300 px-4 py-3 outline-none focus:border-zinc-900"
                value={title}
                onChange={(event) =>
                  setTitle(event.target.value)
                }
                placeholder="Transformer 101"
                maxLength={200}
              />
            </div>

            <div>
              <label className="mb-2 block text-sm font-medium">
                Description
              </label>

              <textarea
                className="min-h-28 w-full rounded-lg border border-zinc-300 px-4 py-3 outline-none focus:border-zinc-900"
                value={description}
                onChange={(event) =>
                  setDescription(event.target.value)
                }
                placeholder="Course description"
              />
            </div>

            <button
              type="submit"
              disabled={creating || !title.trim()}
              className="rounded-lg bg-zinc-950 px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {creating
                ? "Creating..."
                : "Create Course"}
            </button>
          </form>
        </section>


        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-red-700">
            {error}
          </div>
        )}


        <section>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-semibold">
              Your courses
            </h2>

            <button
              onClick={loadCourses}
              className="text-sm font-medium text-zinc-600 hover:text-zinc-950"
            >
              Refresh
            </button>
          </div>

          {loading ? (
            <p className="text-zinc-500">
              Loading courses...
            </p>
          ) : courses.length === 0 ? (
            <div className="rounded-xl border border-dashed border-zinc-300 p-10 text-center text-zinc-500">
              No courses yet.
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2">
              {courses.map((course) => (
                <article
                  key={course.id}
                  className="rounded-2xl border border-zinc-200 bg-white p-6 shadow-sm"
                >
                  <h3 className="text-xl font-semibold">
                    {course.title}
                  </h3>

                  <p className="mt-2 text-sm text-zinc-600">
                    {course.description ||
                      "No description"}
                  </p>

                  <div className="mt-6 flex gap-2 text-xs">
                    <span className="rounded-full bg-zinc-100 px-3 py-1">
                      v{course.version_no ?? "—"}
                    </span>

                    <span className="rounded-full bg-zinc-100 px-3 py-1">
                      {course.version_state ??
                        "unknown"}
                    </span>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
