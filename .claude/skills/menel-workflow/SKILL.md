---
name: menel-workflow
description: Realizacja issues projektu MENEL (org januszex-ai) zgodnie z CONTRIBUTING – issue → branch → implementacja z testami → PR z szablonem → review. Używaj, gdy użytkownik każe wziąć/zrobić issue, zadanie ze sprintu lub tablicy, albo wywoła /menel-workflow <numer|next|all>.
argument-hint: "<numer-issue> | next | all"
---

# MENEL – workflow realizacji issues

Projekt: platforma zgłaszania usterek miejskich (PPSI2 + PIG + WDZPD).
Organizacja: `januszex-ai`, tablica: GitHub Projects `januszex-ai/1`.
Repozytoria: backend (Laravel + PostgreSQL/PostGIS w Dockerze), frontend (React + Vite + TS + Tailwind + Shadcn + mapcn + Storybook), docs (WDZPD, `zaliczenie/`, Astro Starlight).

Argument: `$ARGUMENTS`

## 1. Źródła prawdy (w tej kolejności)

1. Treść issue: zakres, kryteria akceptacji, komentarze.
2. Aktualny kod w repo oraz ADR-y w repo docs (`zaliczenie/`).
3. `CONTRIBUTING.md` organizacji (repo `januszex-ai/.github`) – streszczony niżej.
4. Tablica Miro (backlog/plan) – to plan, nie specyfikacja. Jeśli kłóci się z 1–2 (np. Miro mówi Laravel 11, repo ma inną wersję), idź za repo i opisz rozbieżność w PR.

Jeśli issue jest sprzeczne z ADR, nie implementuj po cichu: skomentuj issue (po angielsku) i pomiń je.

## 2. Tryby

- `<N>` – realizuj dokładnie issue #N w bieżącym repo.
- `next` – weź pierwsze kwalifikujące się issue z kolumny **Todo** (dla bieżącego repo).
- `all` – realizuj po kolei wszystkie kwalifikujące się issues z **Todo**. Każde issue = osobny branch od `main` i osobny PR. Po każdym PR wróć na `main` i bierz następne. Na końcu raport (sekcja 9).
- Brak argumentu – zapytaj, który tryb.

Lista kandydatów: `.claude/skills/menel-workflow/scripts/board.sh list Todo`.

## 3. Kwalifikacja issue (wszystkie warunki muszą być spełnione)

- Otwarte, w bieżącym repo.
- Label `task` lub `bug`. `user-story` tylko wtedy, gdy nie ma otwartych podzadań (sub-issues). `epic` – nigdy bezpośrednio.
- Nieprzypisane albo przypisane do `@me`. **Nigdy nie bierz issue przypisanego do kogoś innego.**
- Wszystkie zależności (sekcja „Dependencies”, „Depends on #N”, „blocked by #N”, parent wymagający wcześniejszego taska) są zamknięte/zmergowane. W trybie `all` issue zależne od PR-a otwartego w tej sesji pomijasz i odnotowujesz w raporcie – nie robisz stacked branchy.
- Zakres jest wystarczająco jasny. Jeśli nie – dodaj komentarz z konkretnymi pytaniami po angielsku (`gh issue comment N --body ...`), pomiń issue, odnotuj w raporcie. Nie zgaduj wymagań.

## 4. Procedura dla jednego issue

**0. Preflight** (raz na sesję + przed każdym issue):
```bash
git status --porcelain            # musi być pusto – inaczej STOP i zapytaj
gh auth status                    # potrzebny scope "project": gh auth refresh -s project
docker compose ps                 # backend: kontenery muszą działać (docker compose up -d)
```

**1. Zrozumienie**
```bash
gh issue view N --comments
```
Przeczytaj też parent (user story / epic), powiązane ADR i istniejący kod w obszarze zmian. Wypisz sobie checklistę „In scope” z issue – to jest Twój zakres, nic ponad.

**2. Przypisanie i tablica**
```bash
gh issue edit N --add-assignee @me
.claude/skills/menel-workflow/scripts/board.sh move N "In Progress"
```

**3. Branch** – zawsze od świeżego `main`:
```bash
git switch main && git pull --ff-only
git switch -c <P><NNN>/<typ>/<opis-kebab-case>
```
- `P` = prefiks repo: `B` backend, `F` frontend, `D` docs; `NNN` = numer issue dopełniony do 3 cyfr. Przykład z CONTRIBUTING: `B012/feature/user-registration`.
- `typ`: `feature` (nowa funkcjonalność), `fix` (bug), `chore` (konfiguracja, zależności, CI, Docker), `docs` (dokumentacja).
- Opis: 2–5 słów po angielsku, małe litery, myślniki.

**4. Implementacja** – tylko zakres issue. Rzeczy zauważone poza zakresem zapisz do raportu końcowego, nie poprawiaj ich w tym PR.

**5. Testy i jakość** – obowiązkowe przed PR (sekcja 5 per repo). Nowa logika = nowe testy. Czerwone testy → napraw; po 3 nieudanych podejściach STOP (sekcja 8).

**6. Commity** – małe i logiczne, Conventional Commits, tryb rozkazujący, po angielsku:
```
<typ>: <opis>
```
Typy: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `ci`, `style`. Dodawaj pliki jawnie (`git add <ścieżki>`), nie `git add -A`. Zawsze `git commit -m "..."`.

**7. Push**
```bash
git push -u origin HEAD
```

**8. Pull request** – tytuł = Conventional Commit, treść = wypełniony szablon organizacji. Zapisz treść do pliku tymczasowego i użyj `--body-file`:
```bash
gh pr create --base main --title "feat: ..." --body-file /tmp/pr-N.md
```
Szablon (zaznaczaj `[x]` tylko to, co faktycznie sprawdziłeś):
```markdown
## Description of changes
<co i dlaczego; kluczowe decyzje techniczne – zespół musi je rozumieć na obronie>

## Related issue
Closes #N

## How to test
1. <konkretne komendy / kroki, np. docker compose exec app php artisan test --filter=...>
2. <ręczna weryfikacja: endpoint, ekran, breakpoint>

## Pre-merge checklist
- [ ] PR title follows the Conventional Commits convention (e.g., `feat: ...`)
- [ ] Code works locally
- [ ] Tests pass; tests for new logic have been added
- [ ] CI is green
- [ ] Documentation (README / API) has been updated, if applicable
- [ ] No secrets or sensitive data in the code
```
„CI is green” zaznaczasz dopiero po `gh pr checks --watch` zakończonym sukcesem (wtedy `gh pr edit --body-file`). Rozbieżności z Miro/ADR i rzeczy niezrobione wpisz w opisie.

**9. Review i tablica**
```bash
gh pr edit --add-reviewer <login>          # wg tabeli w sekcji 7
.claude/skills/menel-workflow/scripts/board.sh move N "Review"
gh pr checks --watch
```

**10. Merge – NIE robisz sam.** Merge wyłącznie na wyraźne polecenie użytkownika, gdy PR ma approve od innej osoby i CI jest zielone:
```bash
gh pr view --json reviewDecision,statusCheckRollup
gh pr merge --squash --delete-branch
```
Issue zamyka się samo przez `Closes #N` – nie zamykaj issues ręcznie.

**11.** `git switch main` i (w trybie `all`) następne issue.

**Język:** wszystko, co trafia na GitHuba (commity, tytuły i opisy PR, issues, komentarze na issues i PR) oraz komentarze w kodzie – po angielsku. Po polsku tylko raport dla użytkownika i teksty UI aplikacji.

## 5. Zasady per repo

### Backend (Laravel, Docker)
- Wszystko przez kontener, nie instaluj PHP/Composera na hoście (bootstrap Laravel Boost z CLAUDE.md wykonuj tylko w kontenerze i tylko gdy issue tego dotyczy):
  ```bash
  docker compose exec -T app php artisan test
  docker compose exec -T app ./vendor/bin/pint --dirty     # formatowanie PSR-12
  docker compose exec -T app ./vendor/bin/pint --test      # musi przejść przed PR
  ```
- API pod `/api/v1/...`, walidacja w `FormRequest`, odpowiedzi przez API Resources, autoryzacja przez Policies/Gates. Błędy API jako JSON (już skonfigurowane w `bootstrap/app.php`).
- Nowa zmiana schematu = nowa migracja. Nigdy nie edytuj migracji, która jest już na `main`. Zapytania przestrzenne przez PostGIS (`ST_DWithin`, indeks GIST) zgodnie z ADR.
- Każdy nowy/zmieniony endpoint: feature test (happy path + błąd walidacji + brak uprawnień) i aktualizacja specyfikacji OpenAPI.
- Nowa zmienna środowiskowa → `.env.example` + tabela zmiennych w README.
- Role: Użytkownik / Pracownik urzędu / Administrator – sprawdzaj uprawnienia zgodnie z `opis.md`/ADR.

### Frontend (React + Vite + TS)
- Uruchom skrypty, które istnieją w `package.json` (sprawdź najpierw): `lint`, `type-check`/`typecheck`, `test`, `build`, `build-storybook`. ESLint + Prettier muszą przejść.
- Wymagania PIG – każdy PR z UI musi je spełniać:
  - używaj komponentów z biblioteki (Shadcn/mapcn w projekcie); nowy reużywalny komponent = komponent w bibliotece + story w Storybooku dla sensownych stanów (default, hover, focus, disabled, error, loading);
  - tylko tokeny (CSS Variables / Tailwind) o nazwach jak w Figma Variables – zero kolorów i odstępów na sztywno;
  - mobile-first; brak poziomego scrolla na 360, 768 i 1280 px; breakpointy zgodne z Figmą;
  - stany ekranu: pusty, ładowanie, błąd, sukces;
  - formularze: etykieta nad polem, walidacja inline (Zod) przy polu z opisem, jak naprawić błąd; akcje nieodwracalne przez AlertDialog; niedostępne akcje wyłączone;
  - kontrast min. 4.5:1 dla tekstu, 3:1 dla elementów UI; kolor nigdy nie jest jedynym nośnikiem informacji (status = etykieta/ikona + kolor);
  - komunikaty po polsku, zrozumiałe dla mieszkańca, bez kodów błędów.

### Docs (WDZPD)
- Wszystkie artefakty w `zaliczenie/` (PRD, persony, user stories, backlog, ADR, DoD, retrospektywy, sprinty). Korzystaj z szablonów w `lab/templates/`.
- Każda istotna decyzja techniczna = nowy ADR (numeracja kolejna, nie nadpisuj starych – zmieniasz status na „Superseded by ADR-XXX”).
- Strona: `cd zaliczenie/docs && npm ci && npm run build` musi przejść; nowa strona musi być w nawigacji (sidebar w `astro.config.mjs` lub autogenerate).

## 6. Wspólna checklista przed otwarciem PR

- [ ] Wszystkie punkty „In scope” z issue zrobione albo jawnie opisane jako niezrobione.
- [ ] Testy i linty zielone lokalnie (komendy z sekcji 5).
- [ ] Brak sekretów, `.env`, kluczy, tokenów, danych osobowych w diffie (`git diff main...HEAD`).
- [ ] README / OpenAPI / dokumentacja zaktualizowane, jeśli zmiana tego dotyczy.
- [ ] Diff czytelny i mały – jeden PR = jedno issue. Duże issue → zaproponuj w raporcie podział zamiast gigantycznego PR.
- [ ] Opis PR wyjaśnia decyzje tak, żeby każdy członek zespołu umiał je obronić.

## 7. Zespół i review

Autor PR nie może zatwierdzić własnych zmian; review w ciągu 24 h.

| Obszar zmian | Reviewer | GitHub login |
|---|---|---|
| Backend / DevOps | Pawel D. | `ziutek22` |
| Backend / DevOps/ Tester | Grzegorz S. | `SlomkaGrzegorz` |
| Frontend / PM / Tester | Kacper B. | `kacperhaha` |
| PM/ Tester | Tobiasz J. | `b0binho` |

Jeśli login to `TODO` – nie zgaduj, pomiń `--add-reviewer` i napisz o tym w raporcie.

## 8. Zakazy i kiedy się zatrzymać

Zakazane (część blokuje też hook `.claude/hooks/guard.py`):
- commit lub push na `main`, force push, `--no-verify`, `--admin` przy merge'u, approve PR-a;
- ręczne zamykanie/usuwanie issues, przypisywanie cudzych issues, zmiana cudzych PR-ów;
- czytanie i commitowanie `.env` oraz sekretów; `docker compose down -v` (kasuje bazę);
- zmiany w `.github/workflows`, branch protection i konfiguracji Dockera, chyba że issue dokładnie tego dotyczy;
- wyłączanie, usuwanie lub osłabianie testów, żeby przeszły.

Zatrzymaj się i zapytaj użytkownika, gdy:
- working tree nie jest czysty na starcie;
- testy nie przechodzą po 3 próbach naprawy – wypchnij branch, otwórz PR jako `--draft` z opisem problemu, przejdź dalej (tryb `all`) lub zakończ;
- issue wymaga decyzji architektonicznej, nowej zależności spoza stacku z ADR albo zmiany schematu sprzecznej z ADR;
- konflikt przy `git pull`/rebase, którego nie da się rozwiązać jednoznacznie.

## 9. Raport końcowy (po polsku, zwięźle)

| Issue | Branch | PR | Status | Uwagi |
|---|---|---|---|---|

Statusy: `PR otwarty (Review)`, `Draft – testy`, `Pominięte – zależność #X`, `Pominięte – pytania na issue`, `Pominięte – cudze`.
Pod tabelą: rzeczy spoza zakresu zauważone po drodze (propozycje nowych issues – nie twórz ich bez zgody) i brakujące loginy reviewerów.