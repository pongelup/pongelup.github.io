# Pending fixes

Source: website audit of 2026-10-09 (`Media\M - Claude Public Relations\pr_website_audit_2026-10-09.html`),
facts file `Webpage\Website Facts 2026-10-09.md`, and Leo's decisions of 2026-10-09.
Ticked items were applied on 2026-10-09 (site and, where relevant, the CV repo). Unticked items still need Leo.

Applied before Leo's decisions (mechanical): DOI links next to publications; per-page `<title>`,
meta description and Open Graph tags; News section driven by `data/news.yml`; alt text on all images.

## A. Contact and identity
- [x] A1. Phone set to +1 (215) 898-7684 (Wharton profile and CV).
- [x] A2. Public email set to pongelup@wharton.upenn.edu (Home contact block and footer).
- [x] A3. Profile links added: Wharton faculty page, Google Scholar, ORCID (0000-0001-6195-4455), SSRN author page, LinkedIn, X. Shown as footer icons on every page and as a "Profiles" line on Home; also in the CV header.
- [x] A4. Twitter icon replaced by an X icon pointing to x.com/LSPongeluppe.
- [x] A5. Insper Metricis: research associate 2016 to present kept; bio says "where he remains a research associate".
- [ ] A6. Favicon: still none. Needs a headshot crop or an "LP" mark from Leo.

## B. Publications (Research page, `data/publications.yml`; CV `03a`, `03b`, `03d`)
- [x] B1. BEQ: 2026, 36(1): 69-111, full title, author "Cook, M. L.".
- [x] B2. O&E: 2026, 39(1): 112-139, comma in "Comprehensive, Direct-Observation".
- [x] B3. ASQ 2024: "Forthcoming" removed.
- [x] B4. Management Science: "William"; stray "Working Paper." removed.
- [x] B5. ReStat: "(2025) ... Published online October 2025." on site and CV (no volume or issue yet). Change to the issue citation when it appears.
- [x] B6. Awards added under the papers: ASQ Dissertation Award 2025; RRBM Micro (MS) and Macro (SMJ) 2025; AMD Best Paper runner-up; AOM Distinguished Paper Award in Cooperative Strategy (BEQ).
- [x] B7. "Ito, N. C., & Pongeluppe, L. S." (was L.P.); RAP 54(4).
- [x] B8. Citation punctuation harmonized (commas, ampersands, "Vol(Issue): pages"). Cordeiro et al. initials G. S. and P. R.
- [x] B9. SSIR: public article page linked ("SSIR" link on the site; title link in the CV).
- [x] B10. ASQ book review: 71(2).
- [x] B11. npj Natural Hazards: "3, Article 20" (was 3(1): 1-20). Title written with a hyphen in "city-river" (house rule; the journal uses a typographic dash).
- [x] B12. BAR: 16(4): e190072. Book chapters: DOIs added for the Elgar and Palgrave chapters (Elgar pages still not found).

## C. Working papers (`data/working_papers.yml`; CV `03c`)
- [x] C1. Site and CV now show the same 11 working papers in the same order, grouped on the site by the three pillars. Each shows title, coauthors, status (journal and round), links, and one research question only (no abstracts, results, or numbers).
- [x] C2. North Star title now matches the CV ("Stakeholder Architecture under Resource Constraints...").
- [x] C3. Desalination abstract removed (question only), so the "adaption" typo is gone.
- [x] C4. Leviathan as A Client: "Second round at Strategic Management Journal"; title ends "to Address Water Scarcity" on both.
- [x] C5. Topic headings renamed to the three pillars.
- [x] C6. Statuses per Leo (2026-10-09): Not from Ipanema "First round at Organization Science"; AMR "Working paper (desk edit at Academy of Management Review)".
- [ ] C7. Leo to eyeball: placement of the AMR paper and #MeToo under "Poverty and Inequality" (pillar renamed 2026-10-09) and of the ESG paper under "Climate Change"; the Fifty Shades results chart (`wp-green-pixels.png`) was dropped from the page because it shows a result; the #MeToo method figure (Walmart report page with detected faces) was NOT posted (third-party image of identifiable people); Daphne Coelho vs Daphne Coelho Dutra.
- [ ] C8. #MeToo status changes to "Under review at Strategic Management Journal" once Michelle submits (planned 10-11 October 2026). Zika ("Who Bears the Epidemic?") not listed: not in the CV, analysis stage.

## D. Teaching (`content/teaching.yml`)
- [x] D1. "Sandro Cabral".
- [x] D2. "Capsim Management Simulator".
- [x] D3. Banco da Providência: now links to the DOI (https://doi.org/10.4135/9798348834449). No token URL anywhere.
- [x] D4. Lions Outback Vision: now links to the DOI (https://doi.org/10.4135/9781071976265).
- [x] D5. Teaching Awards section added with all three Wharton Teaching Excellence Awards (2023-24, 2024-25, 2025-26).

## E. Practice & Media (formerly Extension; `content/extension.yml`, `data/media.yml`)
- [x] E1. Folha: 24 de setembro de 2024.
- [x] E2. BM&C Talks: 16 de julho de 2024.
- [x] E3. "The Burnes Center for Social Change" (site and CV).
- [x] E4. Dead links replaced: SAGE blog (".../converting-a-thesis-dissertation-into-a-manuscript-1"); Rotman "Retailers" and "No planet B" (insightshub.rotman.utoronto.ca); Instituto HG report (ambikira.org.br). Site and CV.
- [x] E5. Insper Metricis Guide: links to the public Portuguese 2018 edition on GIFE Sinapse (site and CV). The English edition has no verified public URL.
- [ ] E6. Amazon Impact Bond still on an old Dropbox "/s/" link (works; fragile). Same for the Accenture reports in the CV.
- [x] E7. Media items added from the CV: Penn Today (Apr 2026), The Conversation Africa (Mar 2026), Penn Today (Dec 2025), Rotman "No planet B" (Apr 2024).
- [x] E8. Nav label renamed "Practice & Media" (audit L4, option A); the URL stays /extension/. "In the Media" now comes first; each report has a visible "Read the report" text link.
- [x] E9. Portuguese list order correct after E1 and E2; stray leading ". " in dates removed.
- [ ] E10. Penn Today days: the CV and site say Dec 18, 2025 and Apr 30, 2026; the facts file reads Dec 17 and Apr 29 (Cloudflare, unconfirmed). Check in a browser.

## F. CV page (`content/cv.yml`)
- [x] F1. The CV page now embeds the PDF compiled from the CV repo (`assets/cv/Leandro_Pongeluppe_CV.pdf`) with a "Download CV (PDF)" button; the Google Drive iframe is gone. Home has a "Download CV (PDF, updated October 2026)" button.
- [x] F2. Rotman link inside the CV fixed (CV repo).
- [x] F3. CV page description: "... Updated October 2026."

## G. CIA Framework (`content/cia-framework.yml`)
- [x] G1. Name: "Comparative Institutional Analysis (CIA) Framework" (site page heading, SEO title, CV item). Nav label and banner keep the short "CIA Framework".
- [x] G2. Three sentences above the app (what, for whom) and a suggested citation, written from the CIA Framework README. Leo to confirm the wording.
- [x] G3. SEO description filled.

## H. Home page (`content/home.yml`, `data/news.yml`)
- [x] H1. News: 16 dated items (month and year from Crossref, SAGE, and outlet metadata); latest 3 on Home, full list on the new /news/ page (in the nav).
- [x] H2. "Recent Highlights" renamed "Talks and Media" and moved below News, Research Program, and Selected Publications.
- [x] H3. Refreshed bio (audit 3a) with journals, awards, editorial boards, teaching awards, Insper Metricis, and a Portuguese paragraph ("Professor Assistente").
- [x] H4. "Research Program" (three lines) and "Selected Publications" (five papers, one-line takeaway for four; BEQ has none because the deck gives none) on Home; full Research Program block on Research (questions only for working papers).
- [ ] H5. News item dated "2026" (SSRN ESG paper): the posting month is unknown (Crossref record created May 2026). Add the month if Leo knows it.

## I. Site-wide
- [x] I1. "Last update: October 2026." on every page.
- [ ] I2. Personal page: #LeoMovieList is a Twitter search that needs an X login; quemsomosnos.com.br unverified.
- [x] I3. Personal page SEO description kept as written ("Personal interests of Leandro S. Pongeluppe: cinema, football, music, and philosophy.").
- [ ] I4. Long pages (Research, Practice & Media) still have no table of contents.
