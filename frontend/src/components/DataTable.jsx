/**
 * Generic table: columns = [{ key, label, render? }], rows = array of objects.
 * `actions(row)` returns an array of {label, icon, onClick} rendered as a
 * row of small buttons - kept simple (no dropdown/kebab) to stay dependency-free.
 */
export default function DataTable({ columns, rows, actions, emptyLabel = 'No records yet.' }) {
  if (!rows || rows.length === 0) {
    return (
      <div className="card p-10 text-center text-gray-400">
        <i className="bi bi-inbox text-2xl" />
        <p className="mt-2 text-sm">{emptyLabel}</p>
      </div>
    )
  }
  return (
    <div className="card overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="bg-gray-50 border-b border-gray-200">
            {columns.map((c) => (
              <th key={c.key} className="text-left font-semibold text-gray-500 uppercase text-xs tracking-wide px-4 py-2.5 whitespace-nowrap">
                {c.label}
              </th>
            ))}
            {actions && <th className="w-1" />}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
              {columns.map((c) => (
                <td key={c.key} className="px-4 py-2.5 text-gray-700 align-middle">
                  {c.render ? c.render(row) : (row[c.key] ?? '—')}
                </td>
              ))}
              {actions && (
                <td className="px-4 py-2.5 text-right whitespace-nowrap">
                  <div className="flex justify-end gap-1">
                    {actions(row).map((a, i) => (
                      <button
                        key={i}
                        onClick={a.onClick}
                        title={a.label}
                        className="w-7 h-7 inline-flex items-center justify-center rounded-md border border-gray-200 text-gray-500 hover:bg-gray-100"
                      >
                        <i className={`bi ${a.icon}`} />
                      </button>
                    ))}
                  </div>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
