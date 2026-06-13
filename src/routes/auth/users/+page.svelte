<script lang="ts">
  import Header from '$lib/components/Header.svelte';

  interface User {
    id: string;
    name: string;
    role: 'admin' | 'learner';
  }

  interface Props {
    data: { users: User[]; currentUserId: string | null };
    form?: { name?: string; error?: string; ok?: boolean };
  }

  let { data, form }: Props = $props();
</script>

<Header crumbs={[{ label: 'Profiles' }]} />

<main class="flex-1 overflow-y-auto px-6 py-8">
  <div class="mx-auto grid w-full max-w-5xl gap-8 lg:grid-cols-[1fr_20rem]">
    <section>
      <h1 class="mb-2 text-2xl font-bold text-slate-100">Profiles</h1>
      <p class="mb-6 max-w-2xl text-sm leading-6 text-slate-400">
        Profiles keep drafts, completions, study history, achievements, run history, and sandbox preferences separate on a shared local server.
      </p>

      <div class="overflow-hidden rounded-lg border border-slate-700">
        {#each data.users as user}
          <div class="flex items-center justify-between border-b border-slate-800 bg-surface-900 px-4 py-3 last:border-b-0">
            <div>
              <p class="font-medium text-slate-100">
                {user.name}
                {#if user.id === data.currentUserId}<span class="ml-2 text-xs text-accent-300">Current</span>{/if}
              </p>
            </div>
          </div>
        {/each}
      </div>
    </section>

    <form method="POST" action="?/create" class="h-fit rounded-lg border border-slate-700 bg-surface-900 p-5">
        <h2 class="mb-4 text-sm font-semibold text-slate-100">Add profile</h2>
        {#if form?.error}
          <p class="mb-4 rounded border border-rose-900 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">{form.error}</p>
        {:else if form?.ok}
          <p class="mb-4 rounded border border-emerald-900 bg-emerald-950/30 px-3 py-2 text-sm text-emerald-200">Profile created.</p>
        {/if}

        <label class="mb-5 block text-sm font-medium text-slate-300">
          Name
          <input name="name" value={form?.name ?? ''} autocomplete="name" class="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" required />
        </label>

        <button class="btn-primary w-full justify-center" type="submit">Add profile</button>
    </form>
  </div>
</main>
