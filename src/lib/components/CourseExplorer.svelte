<script lang="ts">
  import type { ProblemMeta, Track } from '$lib/types/course.js';

  export interface ExplorerSection {
    id: string;
    label: string;
    content: string;
  }

  interface Heading {
    id: string;
    sectionId: string;
    text: string;
    level: number;
  }

  interface Props {
    track: Track;
    currentSlug: string;
    sections: ExplorerSection[];
    activeSectionId?: string;
    activeHeadingId?: string;
    open?: boolean;
    onsection?: (sectionId: string) => void;
    onheading?: (sectionId: string, headingId: string) => void;
  }

  let {
    track,
    currentSlug,
    sections,
    activeSectionId = '',
    activeHeadingId = '',
    open = $bindable(true),
    onsection,
    onheading
  }: Props = $props();

  let query = $state('');
  let moduleSectionsOpen = $state(true);
  let expandedSectionIds = $state<string[]>([]);
  let expandedSectionsForSlug = $state('');

  function slugify(text: string): string {
    const slug = text
      .toLowerCase()
      .replace(/<[^>]+>/g, '')
      .replace(/[`*_~[\]()]/g, '')
      .replace(/&[a-z0-9#]+;/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '');
    return slug || 'section';
  }

  function cleanHeading(text: string): string {
    return text
      .replace(/!\[[^\]]*]\([^)]*\)/g, '')
      .replace(/\[([^\]]+)]\([^)]*\)/g, '$1')
      .replace(/[`*_~]/g, '')
      .replace(/#+\s*$/g, '')
      .trim();
  }

  function extractHeadings(section: ExplorerSection): Heading[] {
    const headings: Heading[] = [];
    const seen = new Map<string, number>();
    let inFence = false;

    for (const rawLine of section.content.split(/\r?\n/)) {
      const line = rawLine.trim();
      if (line.startsWith('```') || line.startsWith('~~~')) {
        inFence = !inFence;
        continue;
      }
      if (inFence) continue;

      const match = /^(#{1,4})\s+(.+)$/.exec(line);
      if (!match) continue;

      const text = cleanHeading(match[2]);
      if (!text) continue;

      const base = `${section.id}-${slugify(text)}`;
      const count = seen.get(base) ?? 0;
      seen.set(base, count + 1);

      headings.push({
        id: count === 0 ? base : `${base}-${count + 1}`,
        sectionId: section.id,
        text,
        level: match[1].length
      });
    }

    return headings;
  }

  let sectionHeadings = $derived.by(() => {
    const map = new Map<string, Heading[]>();
    for (const section of sections) map.set(section.id, extractHeadings(section));
    return map;
  });
  let allHeadings = $derived.by(() => sections.flatMap((section) => sectionHeadings.get(section.id) ?? []));
  let q = $derived(query.trim().toLowerCase());
  let currentModule = $derived(track.problems.find((problem) => problem.slug === currentSlug));

  let visibleSections = $derived.by(() => {
    if (!q) return sections;
    return sections.filter((section) => {
      if (section.label.toLowerCase().includes(q)) return true;
      return (sectionHeadings.get(section.id) ?? []).some((heading) => heading.text.toLowerCase().includes(q));
    });
  });

  let hasSectionMatch = $derived(visibleSections.length > 0);
  let activeSection = $derived(sections.find((section) => section.id === activeSectionId));

  let matchingModules = $derived.by(() => {
    if (!q) return track.problems;
    return track.problems.filter((problem) => {
      if (problem.slug === currentSlug && hasSectionMatch) return true;
      return [
        problem.title,
        problem.description,
        problem.type,
        problem.difficulty,
        ...problem.tags
      ].some((value) => value.toLowerCase().includes(q));
    });
  });

  let hasHeadingMatch = $derived.by(() => {
    if (!q) return allHeadings.length > 0;
    return allHeadings.some((heading) => heading.text.toLowerCase().includes(q));
  });

  $effect(() => {
    if (expandedSectionsForSlug === currentSlug) return;
    const firstSectionId = activeSectionId || sections[0]?.id;
    expandedSectionIds = firstSectionId ? [firstSectionId] : [];
    expandedSectionsForSlug = currentSlug;
    moduleSectionsOpen = true;
  });

  $effect(() => {
    if (q) moduleSectionsOpen = true;
  });

  $effect(() => {
    if (!activeHeadingId) return;
    const heading = allHeadings.find((item) => item.id === activeHeadingId);
    if (!heading || expandedSectionIds.includes(heading.sectionId)) return;
    expandedSectionIds = [...expandedSectionIds, heading.sectionId];
  });

  function moduleKind(problem: ProblemMeta): string {
    if (problem.type === 'reading') return 'Read';
    if (problem.type === 'quiz') return 'Quiz';
    if (problem.type === 'test') return 'Test';
    if (problem.type === 'drill') return 'Drill';
    return 'Code';
  }

  function isSectionExpanded(sectionId: string): boolean {
    return expandedSectionIds.includes(sectionId);
  }

  function toggleSection(sectionId: string) {
    if (isSectionExpanded(sectionId)) {
      expandedSectionIds = expandedSectionIds.filter((id) => id !== sectionId);
    } else {
      expandedSectionIds = [...expandedSectionIds, sectionId];
    }
  }
</script>

<aside class="course-explorer" class:collapsed={!open} aria-label="Course explorer">
  {#if !open}
    <button
      type="button"
      class="explorer-reopen"
      onclick={() => (open = true)}
      aria-label="Open course explorer"
      title="Open course explorer"
    >
      <svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M4 6h16" />
        <path d="M4 12h12" />
        <path d="M4 18h8" />
      </svg>
    </button>
  {:else}
    <div class="explorer-top">
      <div class="explorer-title">
        <span class="explorer-kicker">Explorer</span>
        <span>{currentModule?.title ?? track.title}</span>
      </div>
      <button
        type="button"
        class="explorer-hide"
        onclick={() => (open = false)}
        aria-label="Hide course explorer"
        title="Hide course explorer"
      >
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M15 18l-6-6 6-6" />
        </svg>
      </button>
    </div>

    <div class="explorer-search">
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="11" cy="11" r="7" />
        <path d="M20 20l-3.5-3.5" />
      </svg>
      <input
        bind:value={query}
        type="search"
        placeholder="Search course"
        aria-label="Search course"
      />
    </div>

    <div class="explorer-scroll">
      <section class="explorer-section">
        <div class="explorer-label">Course outline</div>
        <div class="explorer-list">
          {#each matchingModules as module}
            {@const isCurrent = module.slug === currentSlug}
            <div class="module-group">
              <div class="module-row" class:current={isCurrent}>
                <a
                  class="module-link"
                  href="/tracks/{track.slug}/problems/{module.slug}"
                  aria-current={isCurrent ? 'page' : undefined}
                >
                  <span class="module-order">{String(module.order).padStart(2, '0')}</span>
                  <span class="module-copy">
                    <span class="module-title">{module.title}</span>
                    <span class="module-meta">
                      {moduleKind(module)} / {module.estimatedMinutes}m
                      {#if isCurrent && activeSection}
                        <span class="module-dot" aria-hidden="true"></span>{activeSection.label}
                      {/if}
                    </span>
                  </span>
                </a>
                {#if isCurrent && sections.length > 0}
                  <button
                    type="button"
                    class="module-toggle"
                    class:open={moduleSectionsOpen}
                    onclick={() => (moduleSectionsOpen = !moduleSectionsOpen)}
                    aria-label={moduleSectionsOpen ? 'Collapse module sections' : 'Expand module sections'}
                    aria-expanded={moduleSectionsOpen}
                    title={moduleSectionsOpen ? 'Collapse sections' : 'Expand sections'}
                  >
                    <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                      <path d="M9 18l6-6-6-6" />
                    </svg>
                  </button>
                {/if}
              </div>

              {#if isCurrent && moduleSectionsOpen}
                <div class="section-nest">
                {#each visibleSections as section}
                  {@const headingsForSection = q
                    ? (sectionHeadings.get(section.id) ?? []).filter((heading) => heading.text.toLowerCase().includes(q))
                    : (sectionHeadings.get(section.id) ?? [])}
                  {@const sectionExpanded = isSectionExpanded(section.id)}
                  <div class="chapter-group">
                    <div class="section-row" class:active={activeSectionId === section.id}>
                      <button
                        type="button"
                        class="explorer-section-link"
                        onclick={() => onsection?.(section.id)}
                        title={section.label}
                      >
                        <span>{section.label}</span>
                      </button>

                      {#if headingsForSection.length > 0}
                        <button
                          type="button"
                          class="section-toggle"
                          class:open={sectionExpanded}
                          onclick={() => toggleSection(section.id)}
                          aria-label={sectionExpanded ? `Collapse ${section.label} headings` : `Expand ${section.label} headings`}
                          aria-expanded={sectionExpanded}
                          title={sectionExpanded ? 'Collapse headings' : 'Expand headings'}
                        >
                          <svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                            <path d="M9 18l6-6-6-6" />
                          </svg>
                        </button>
                      {/if}
                    </div>

                    {#if headingsForSection.length > 0 && sectionExpanded}
                      <div class="heading-nest">
                        {#each headingsForSection as heading}
                          <button
                            type="button"
                            class="heading-link level-{Math.min(heading.level, 4)}"
                            class:active={activeHeadingId === heading.id}
                            onclick={() => onheading?.(heading.sectionId, heading.id)}
                            title={heading.text}
                            aria-current={activeHeadingId === heading.id ? 'location' : undefined}
                          >
                            <span>{heading.text}</span>
                          </button>
                        {/each}
                      </div>
                    {/if}
                  </div>
                {/each}

                {#if visibleSections.length === 0 || (q && !hasHeadingMatch)}
                  <p class="explorer-empty">No matching sections.</p>
                {/if}
                </div>
              {/if}
            </div>
          {/each}
          {#if matchingModules.length === 0}
            <p class="explorer-empty">No matching modules.</p>
          {/if}
        </div>
      </section>
    </div>
  {/if}
</aside>

<style>
  .course-explorer {
    width: 230px;
    flex: 0 0 230px;
    min-height: 0;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #1e293b;
    background: #10141d;
  }

  .course-explorer.collapsed {
    width: 42px;
    flex-basis: 42px;
    align-items: center;
    padding-top: 0.65rem;
  }

  .explorer-reopen,
  .explorer-hide {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: 1px solid #263449;
    border-radius: 6px;
    background: #0d1117;
    color: #94a3b8;
    cursor: pointer;
  }

  .explorer-reopen:hover,
  .explorer-hide:hover {
    border-color: #60a5fa;
    color: #dbeafe;
    background: #172033;
  }

  .explorer-top {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.75rem 0.75rem 0;
    flex-shrink: 0;
  }

  .explorer-title {
    min-width: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    color: #e2e8f0;
    font-size: 0.78rem;
    font-weight: 650;
    line-height: 1.25;
  }

  .explorer-title span:last-child {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .explorer-kicker {
    color: #64748b;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .explorer-hide {
    width: 26px;
    height: 26px;
    flex: 0 0 26px;
  }

  .explorer-search {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    margin: 0.75rem;
    padding: 0.45rem 0.55rem;
    border: 1px solid #263449;
    border-radius: 7px;
    background: #0d1117;
    color: #64748b;
    flex-shrink: 0;
  }

  .explorer-search:focus-within {
    border-color: #60a5fa;
    color: #93c5fd;
  }

  .explorer-search input {
    width: 100%;
    min-width: 0;
    border: 0;
    outline: 0;
    background: transparent;
    color: #e2e8f0;
    font-size: 0.78rem;
  }

  .explorer-search input::placeholder {
    color: #64748b;
  }

  .explorer-scroll {
    min-height: 0;
    overflow-y: auto;
    padding: 0 0.5rem 0.85rem;
  }

  .explorer-label {
    margin: 0 0.4rem 0.4rem;
    color: #64748b;
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }

  .explorer-list,
  .module-group,
  .chapter-group {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }

  .module-group {
    gap: 0.16rem;
  }

  .heading-nest {
    margin-left: 0.62rem;
    padding-left: 0.45rem;
    border-left: 1px solid #263449;
  }

  .section-nest {
    margin: 0 0.08rem 0.22rem 1.08rem;
    padding: 0.18rem 0 0.22rem 0.48rem;
    border-left: 1px solid #263449;
  }

  .explorer-section-link,
  .heading-link,
  .module-link,
  .module-toggle,
  .section-toggle {
    border: 0;
    border-radius: 6px;
    background: transparent;
    color: #94a3b8;
    text-align: left;
    text-decoration: none;
    cursor: pointer;
    transition: background 120ms ease, color 120ms ease;
  }

  .explorer-section-link:hover,
  .heading-link:hover,
  .module-row:hover,
  .section-row:hover {
    background: #1a2230;
    color: #e2e8f0;
  }

  .section-row,
  .module-row {
    display: flex;
    align-items: center;
    border-radius: 6px;
    color: #94a3b8;
    transition: background 120ms ease, color 120ms ease;
  }

  .section-row.active {
    background: rgba(96, 165, 250, 0.12);
    color: #bfdbfe;
  }

  .explorer-section-link {
    display: flex;
    align-items: center;
    min-width: 0;
    flex: 1;
    padding: 0.32rem 0.42rem;
    font-size: 0.75rem;
    font-weight: 650;
  }

  .explorer-section-link span,
  .heading-link span {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .explorer-section-link span {
    white-space: nowrap;
  }

  .heading-link {
    position: relative;
    display: block;
    width: 100%;
    padding: 0.27rem 0.42rem;
    font-size: 0.71rem;
    line-height: 1.35;
  }

  .heading-link.active {
    background: rgba(14, 165, 233, 0.14);
    color: #e0f2fe;
  }

  .heading-link.active::before {
    content: '';
    position: absolute;
    top: 0.45rem;
    bottom: 0.45rem;
    left: -0.48rem;
    width: 2px;
    border-radius: 999px;
    background: #38bdf8;
  }

  .level-1 { padding-left: 0.45rem; font-weight: 650; color: #cbd5e1; }
  .level-2 { padding-left: 0.65rem; }
  .level-3 { padding-left: 0.95rem; color: #7f8ea3; }
  .level-4 { padding-left: 1.2rem; color: #64748b; }

  .module-row.current {
    background: rgba(96, 165, 250, 0.1);
    color: #dbeafe;
  }

  .module-link {
    display: flex;
    min-width: 0;
    flex: 1;
    gap: 0.5rem;
    padding: 0.42rem 0.44rem;
  }

  .module-order {
    width: 1.45rem;
    flex: 0 0 1.45rem;
    color: #64748b;
    font-family: 'JetBrains Mono', ui-monospace, monospace;
    font-size: 0.68rem;
    line-height: 1.35rem;
    text-align: right;
  }

  .module-copy {
    min-width: 0;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }

  .module-title {
    overflow: hidden;
    color: inherit;
    font-size: 0.76rem;
    font-weight: 600;
    line-height: 1.25;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .module-meta {
    display: flex;
    align-items: center;
    min-width: 0;
    gap: 0.28rem;
    overflow: hidden;
    color: #64748b;
    font-size: 0.66rem;
    line-height: 1.2;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .module-dot {
    width: 3px;
    height: 3px;
    flex: 0 0 3px;
    border-radius: 999px;
    background: #475569;
  }

  .module-toggle,
  .section-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 1.45rem;
    height: 1.45rem;
    flex: 0 0 1.45rem;
    margin-right: 0.18rem;
    color: #64748b;
  }

  .section-toggle {
    width: 1.25rem;
    height: 1.25rem;
    flex-basis: 1.25rem;
  }

  .module-toggle:hover,
  .section-toggle:hover {
    background: rgba(96, 165, 250, 0.12);
    color: #bfdbfe;
  }

  .module-toggle svg,
  .section-toggle svg {
    transition: transform 130ms ease;
  }

  .module-toggle.open svg,
  .section-toggle.open svg {
    transform: rotate(90deg);
  }

  .explorer-empty {
    margin: 0.35rem 0.45rem;
    color: #64748b;
    font-size: 0.74rem;
    font-style: italic;
  }

  @media (max-width: 1100px) {
    .course-explorer {
      display: none;
    }
  }
</style>
