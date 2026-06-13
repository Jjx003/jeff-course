<script lang="ts">
  import { enhance } from '$app/forms';
  import { APP_NAME } from '$lib/config/app.js';

  interface Props {
    form?: { name?: string; error?: string };
  }

  let { form }: Props = $props();
</script>

<main class="min-h-dvh overflow-y-auto bg-slate-950 px-6 py-12 text-slate-100">
  <section class="mx-auto flex w-full max-w-sm flex-col gap-6">
    <div>
      <p class="mb-2 text-sm font-semibold text-accent-300">First profile</p>
      <h1 class="text-2xl font-bold tracking-tight">{APP_NAME}</h1>
      <p class="mt-3 text-sm leading-6 text-slate-400">
        Create the first learner profile. Existing single-learner progress, if any, belongs to this profile.
      </p>
    </div>

    <form method="POST" use:enhance class="rounded-lg border border-slate-700 bg-surface-900 p-5">
      {#if form?.error}
        <p class="mb-4 rounded border border-rose-900 bg-rose-950/40 px-3 py-2 text-sm text-rose-200">{form.error}</p>
      {/if}

      <label class="mb-4 block text-sm font-medium text-slate-300">
        Name
        <input name="name" value={form?.name ?? ''} autocomplete="name" class="mt-1 w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-slate-100" required />
      </label>

      <button class="btn-primary w-full justify-center" type="submit">Create profile</button>
    </form>
  </section>
</main>
