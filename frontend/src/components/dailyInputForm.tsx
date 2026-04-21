import { useState } from "react"
import { useForm, useFieldArray, Controller } from "react-hook-form"

type FormValues = {
  lastPeriodDate: string
  foods: { item: string }[]
  sleepHours: number
  sleepMinutes: number
  waterConsumed: number
  stressLevel: number
}

const today = new Date().toISOString().slice(0, 10)

export const InputForm = () => {
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<string | null>(null)

  const { register, handleSubmit, control } = useForm<FormValues>({
    defaultValues: {
      lastPeriodDate: today,
      foods: [{ item: "" }],
      sleepHours: 8,
      sleepMinutes: 0,
      waterConsumed: 0,
      stressLevel: 3,
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: "foods" })

  const onSubmit = async (data: FormValues) => {
    setSubmitting(true)
    setResult(null)
    try {
      const payload = {
        lastPeriodDate: data.lastPeriodDate,
        foods: data.foods.map((f) => f.item).filter(Boolean),
        sleepHours: Number(data.sleepHours),
        sleepMinutes: Number(data.sleepMinutes),
        waterConsumed: Number(data.waterConsumed),
        stressLevel: Number(data.stressLevel),
      }
      const res = await fetch("/api/analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!res.ok) throw new Error(`Request failed: ${res.status}`)
      const json = await res.json()
      setResult(JSON.stringify(json))
    } catch (err) {
      setResult(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-xl rounded-2xl bg-white p-8 shadow-lg ring-1 ring-pink-100">
      <h2 className="mb-6 text-2xl font-semibold text-pink-700">Daily Check-in</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Last period date
          </label>
          <input
            type="date"
            {...register("lastPeriodDate", { required: true })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-200"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Food I had today
          </label>
          <div className="space-y-2">
            {fields.map((field, index) => (
              <div key={field.id} className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g. oatmeal"
                  {...register(`foods.${index}.item` as const)}
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-200"
                />
                {fields.length > 1 && (
                  <button
                    type="button"
                    onClick={() => remove(index)}
                    className="rounded-lg px-3 py-2 text-sm text-gray-500 hover:bg-gray-100"
                  >
                    Remove
                  </button>
                )}
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={() => append({ item: "" })}
            className="mt-2 rounded-lg bg-pink-50 px-3 py-1.5 text-sm font-medium text-pink-700 hover:bg-pink-100"
          >
            + Add food
          </button>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Sleep
          </label>
          <div className="flex gap-3">
            <div className="flex-1">
              <input
                type="number"
                min={0}
                max={24}
                {...register("sleepHours", { valueAsNumber: true })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-200"
              />
              <span className="mt-1 block text-xs text-gray-500">hours</span>
            </div>
            <div className="flex-1">
              <input
                type="number"
                min={0}
                max={59}
                {...register("sleepMinutes", { valueAsNumber: true })}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-200"
              />
              <span className="mt-1 block text-xs text-gray-500">minutes</span>
            </div>
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Water consumed (glasses)
          </label>
          <input
            type="number"
            min={0}
            {...register("waterConsumed", { valueAsNumber: true })}
            className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-pink-500 focus:outline-none focus:ring-2 focus:ring-pink-200"
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-medium text-gray-700">
            Stress level
          </label>
          <Controller
            control={control}
            name="stressLevel"
            render={({ field }) => (
              <div className="flex gap-2">
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    type="button"
                    onClick={() => field.onChange(n)}
                    className={`h-10 w-10 rounded-full text-sm font-semibold transition ${
                      field.value === n
                        ? "bg-pink-600 text-white shadow"
                        : "bg-gray-100 text-gray-600 hover:bg-pink-100"
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            )}
          />
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded-lg bg-pink-600 py-3 font-semibold text-white shadow hover:bg-pink-700 disabled:cursor-not-allowed disabled:bg-pink-300"
        >
          {submitting ? "Analyzing..." : "Check analysis"}
        </button>

        {result && (
          <pre className="max-h-48 overflow-auto rounded-lg bg-gray-50 p-3 text-xs text-gray-700">
            {result}
          </pre>
        )}
      </form>
    </div>
  )
}
