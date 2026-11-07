// Single-column brief layout for mobile
// Authority: U-014, REMEDIATION_02_Product_Design.md §7

interface Section {
  key: string;
  title: string;
  content: string;
  state: 'AVAILABLE' | 'STALE' | 'UNAVAILABLE';
  sources: Array<{ id: string; origin: string; as_of: string | null }>;
}

interface Brief {
  id: string;
  clientName: string;
  version: string;
  sections: Section[];
}

interface MobileBriefViewProps {
  brief: Brief;
  onSectionReview?: (sectionKey: string) => void;
}

export default function MobileBriefView({ brief, onSectionReview }: MobileBriefViewProps) {
  const stateColors = {
    AVAILABLE: 'border-green-500',
    STALE: 'border-yellow-500',
    UNAVAILABLE: 'border-red-500',
  };

  return (
    <div className="mobile-full">
      {/* Brief header */}
      <div className="bg-white border-b border-capco-gray-200 px-4 py-3 sticky top-0 z-10">
        <h1 className="text-lg font-semibold text-capco-black">{brief.clientName}</h1>
        <p className="text-sm text-capco-gray-600">Version {brief.version}</p>
      </div>

      {/* Sections in single column */}
      <div className="space-y-4 p-4">
        {brief.sections.map((section) => (
          <section
            key={section.key}
            className={`mobile-card border-l-4 ${stateColors[section.state]}`}
          >
            {/* Section header */}
            <div className="mb-3">
              <h2 className="text-base font-semibold text-capco-black mb-1">
                {section.title}
              </h2>
              <div className="flex items-center gap-2 text-xs text-capco-gray-600">
                <span className="capitalize">{section.state.toLowerCase()}</span>
                {section.sources.length > 0 && (
                  <>
                    <span>•</span>
                    <span>{section.sources.length} source{section.sources.length !== 1 ? 's' : ''}</span>
                  </>
                )}
              </div>
            </div>

            {/* Section content */}
            <div className="text-sm text-capco-gray-700 mb-3 whitespace-pre-wrap">
              {section.content}
            </div>

            {/* Sources */}
            {section.sources.length > 0 && (
              <details className="text-xs text-capco-gray-600 mb-3">
                <summary className="cursor-pointer font-medium">View sources</summary>
                <ul className="mt-2 space-y-1 pl-4">
                  {section.sources.map((source) => (
                    <li key={source.id} className="list-disc">
                      <span className="capitalize">{source.origin.toLowerCase()}</span>
                      {source.as_of && (
                        <span className="text-capco-gray-500"> • {source.as_of}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </details>
            )}

            {/* Review action */}
            {onSectionReview && (
              <button
                onClick={() => onSectionReview(section.key)}
                className="btn-touch w-full bg-capco-gray-100 text-capco-black hover:bg-capco-gray-200"
              >
                Review section
              </button>
            )}
          </section>
        ))}
      </div>
    </div>
  );
}
