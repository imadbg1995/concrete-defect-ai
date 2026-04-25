/* ── Bilingual EN / FR ──────────────────────────────────────── */
(function () {
  const T = {
    en: {
      /* Nav */
      'nav.features':      'Features',
      'nav.how':           'How it works',
      'nav.classif':       'Classification',
      'nav.analyzer':      'Analyzer',
      'nav.signin':        'Sign In',
      'nav.started':       'Get Started Free',
      'nav.openapp':       'Open App',
      'nav.signout':       'Sign Out',
      'nav.back':          '← Back to home',

      /* Hero */
      'hero.eyebrow':      'AI-Powered Structural Inspection',
      'hero.title':        'Concrete pathology analysis in <em>seconds</em>',
      'hero.desc':         'Upload a site photo — receive a color-coded defect map and a structured 8-section engineering report. Built for inspectors, engineers, and infrastructure owners.',
      'hero.check1':       'Color-coded crack map by width',
      'hero.check2':       '8-section engineering report',
      'hero.check3':       'Severity & PCI classification',
      'hero.check4':       'Root cause analysis',
      'hero.check5':       'One-click PDF export',
      'hero.cta1':         'Start Free — 3 Analyses Included',
      'hero.cta2':         'See the process',

      /* Stats */
      'stat.defects':      'Defect types recognized',
      'stat.time':         'Report generation time',
      'stat.widths':       'Crack width categories',
      'stat.sections':     'Report sections per analysis',

      /* Features */
      'feat.label':        'Capabilities',
      'feat.heading':      'Everything needed for concrete pathology',
      'feat1.title':       'Multi-type Defect Detection',
      'feat1.desc':        'Identifies cracks, spalling, delamination, carbonation, rebar corrosion, efflorescence, ASR map cracking, and voids from a single photograph.',
      'feat2.title':       '8-Section Engineering Reports',
      'feat2.desc':        'Structured reports covering defect classification, visual observations, root cause analysis, severity assessment, structural risk, repair strategy, monitoring, and condition rating.',
      'feat3.title':       'Context-Aware Analysis',
      'feat3.desc':        '7-field site questionnaire feeds the AI — element type, exposure conditions, structure age, prior repairs, water infiltration, and more — producing far more accurate assessments than photo-only tools.',
      'feat4.title':       'Color-Coded AI Defect Map',
      'feat4.desc':        'Our vision AI paints a precise overlay directly on your photo. Cracks are color-coded by measured width: cyan (hairline <0.5 mm), yellow (medium 0.5–2 mm), orange (wide >2 mm), magenta fills for spalling zones.',
      'feat5.title':       'One-Click PDF Export',
      'feat5.desc':        'Download a complete PDF including both the original and annotated images, the full 8-section structured report, and a professional disclaimer — ready to share with clients or file in project records.',
      'feat6.title':       'Field-Ready Interface',
      'feat6.desc':        'Works on any device. Upload directly from your phone on-site and get a full report before you leave. No installation, no plugins — just a browser.',

      /* How it works */
      'how.label':         'Process',
      'how.heading':       'From field photo to engineering report',
      'how.step1.title':   'Upload the site photograph',
      'how.step1.desc':    'Drag and drop or click to upload any photo of a concrete surface. JPEG, PNG, and WebP supported up to 10 MB.',
      'how.step2.title':   'Complete the site questionnaire',
      'how.step2.desc':    'Answer 7 quick questions — element type, age, exposure conditions, water infiltration, prior repairs. Context significantly improves accuracy.',
      'how.step3.title':   'AI produces the engineering report',
      'how.step3.desc':    'Our AI analyzes the image and questionnaire together, producing a structured 8-section pathology report with defect classification, root cause analysis, and repair strategy.',
      'how.step4.title':   'AI paints the color-coded defect map',
      'how.step4.desc':    'The original photo is processed by our vision engine, which traces every crack and fills every spalled zone with precise color-coded overlays — classified by measured width.',

      /* Classification */
      'cl.label':          'Defect Classification',
      'cl.heading':        'Color-coded by crack width',
      'cl.desc':           'Every crack is visually classified by its measured width. The overlay uses four distinct colors so severity is instantly readable on-site.',
      'cl.color':          'COLOR',
      'cl.cat':            'CATEGORY',
      'cl.width':          'WIDTH THRESHOLD',
      'cl.cause':          'TYPICAL CAUSE',
      'cl.hair':           'Hairline / Fine',
      'cl.med':            'Medium crack',
      'cl.wide':           'Wide crack',
      'cl.spal':           'Spalling zone',
      'cl.cause1':         'Shrinkage, thermal movement, early-age stress',
      'cl.cause2':         'Structural loading, ASR, carbonation-induced',
      'cl.cause3':         'Overloading, rebar corrosion, structural distress',
      'cl.cause4':         'Delamination, freeze-thaw damage, rebar corrosion pressure',
      'cl.note':           'Width classification is performed visually by our AI engine. All results must be verified on-site by a licensed structural engineer. This tool does not replace professional inspection.',

      /* Testimonials */
      'trust.label':       'Trusted by professionals',
      'trust.heading':     'What field engineers say',

      /* Analyzer section */
      'az.label':          'Live Analysis',
      'az.heading':        'Inspect a concrete surface now',
      'az.desc':           'Upload any photo of a concrete surface, complete the site questionnaire, and receive a structured pathology report and color-coded defect map in under a minute.',
      'gate.title':        'Sign in to run an analysis',
      'gate.desc':         'Create a free account and get <strong>3 analyses included</strong> — no credit card required.',
      'gate.btn':          'Sign In / Create Account',
      'gate.f1':           '✓ Color-coded defect map',
      'gate.f2':           '✓ 8-section engineering report',
      'gate.f3':           '✓ PDF export',

      /* CTA section */
      'cta.label':         'Start inspecting',
      'cta.heading':       'Accelerate your field assessments',
      'cta.desc':          'Upload a photo and get a structured pathology report in under 60 seconds.',
      'cta.btn1':          'Start Free Analysis',
      'cta.btn2':          'Contact us',

      /* Footer */
      'foot.product':      'Product',
      'foot.method':       'Methodology',
      'foot.company':      'Company',
      'foot.contact':      'Contact',
      'foot.privacy':      'Privacy Policy',
      'foot.terms':        'Terms of Service',
      'foot.copy':         '© 2026 Concrete Defect AI. All rights reserved.',
      'foot.tag':          'AI-assisted · Not a stamped engineering report',

      /* Login page */
      'login.tab.in':      'Sign In',
      'login.tab.reg':     'Create Account',
      'login.email':       'Email address',
      'login.email.ph':    'you@example.com',
      'login.pass':        'Password',
      'login.pass.ph':     'Min. 6 characters',
      'login.pass2':       'Confirm password',
      'login.pass2.ph':    'Repeat your password',
      'login.country':     'Country',
      'login.country.ph':  'Select country…',
      'login.phone':       'Phone number',
      'login.phone.ph':    '+1 555 000 0000',
      'login.privacy.lbl': 'I have read and agree to the <a href="/privacy" target="_blank" style="color:var(--accent-2);">Privacy Policy</a> — including the collection of my email, country, and phone number.',
      'login.terms.lbl':   'I have read and agree to the <a href="/terms" target="_blank" style="color:var(--accent-2);">Terms of Service</a> — including that AI outputs are not certified engineering documents.',
      'login.btn.in':      'Sign In',
      'login.btn.reg':     'Create Account',
      'login.foot.new':    'New here? <a href="#" onclick="switchTab(\'register\');return false;" style="color:var(--accent-2);">Create a free account</a> — includes 3 analyses.',
      'login.foot.have':   'Already have an account? <a href="#" onclick="switchTab(\'login\');return false;" style="color:var(--accent-2);">Sign in</a>',
      'login.headline':    'Professional concrete inspection, powered by <em>AI</em>',
      'login.sub':         'Upload a photo and receive a structured 8-section pathology report with a color-coded defect map — in under 60 seconds.',
      'login.perk1':       '3 free analyses included with every account',
      'login.perk2':       'Color-coded crack map by severity',
      'login.perk3':       'Root cause analysis & repair strategy',
      'login.perk4':       'One-click PDF export',
      'login.perk5':       'No credit card required',

      /* App page */
      'app.tool':          'Analysis Tool',
      'app.heading':       'Concrete Defect Analysis',
      'app.sub':           'Upload a site photo, fill in the site context, and receive your report in under 60 seconds.',
      'app.signout':       'Sign Out',
      'app.delete':        'Delete Account',
      'app.upload.lbl':    'Click to upload or drag and drop',
      'app.upload.hint':   'JPEG, PNG, WebP — Max 10 MB',
      'app.q.title':       'Site Context Questionnaire',
      'app.q.desc':        'Context significantly improves report accuracy — takes 30 seconds.',
      'app.q.element':     'Element Type',
      'app.q.age':         'Approximate Age',
      'app.q.age.ph':      'e.g. 25 years',
      'app.q.exposure':    'Exposure Conditions',
      'app.q.water':       'Water Infiltration Visible?',
      'app.q.evolving':    'Is the Defect Evolving?',
      'app.q.repair':      'Previous Repair Attempted?',
      'app.q.notes':       'Inspector Notes',
      'app.q.notes.ph':    'Observations: when it appeared, rust stains, leaks, load history, vibrations…',
      'app.submit':        'Generate Report & Defect Map',
      'app.step1':         'Analyzing image',
      'app.step2':         'Mapping defects',
      'app.step3':         'Report ready',
      'app.photo.lbl':     'UPLOADED PHOTO',
      'app.map.lbl':       'AI DEFECT MAP',
      'app.pdf':           '⬇ Download PDF',
      'app.report.lbl':    'AI Assessment Report',
      'app.annot.note':    'AI-generated overlay. Must be verified on-site by a licensed structural engineer.',
      'app.tries':         (n) => n + (n === 1 ? ' analysis' : ' analyses') + ' left',
    },

    fr: {
      /* Nav */
      'nav.features':      'Fonctionnalités',
      'nav.how':           'Comment ça marche',
      'nav.classif':       'Classification',
      'nav.analyzer':      'Analyseur',
      'nav.signin':        'Se connecter',
      'nav.started':       'Commencer gratuitement',
      'nav.openapp':       'Ouvrir l\'application',
      'nav.signout':       'Se déconnecter',
      'nav.back':          '← Retour à l\'accueil',

      /* Hero */
      'hero.eyebrow':      'Inspection structurale par IA',
      'hero.title':        'Analyse pathologique du béton en <em>quelques secondes</em>',
      'hero.desc':         'Téléchargez une photo de chantier — recevez une carte de défauts codée par couleur et un rapport d\'ingénierie structuré en 8 sections. Conçu pour les inspecteurs, ingénieurs et propriétaires d\'infrastructures.',
      'hero.check1':       'Carte des fissures codée par largeur',
      'hero.check2':       'Rapport d\'ingénierie en 8 sections',
      'hero.check3':       'Classification sévérité & PCI',
      'hero.check4':       'Analyse des causes profondes',
      'hero.check5':       'Export PDF en un clic',
      'hero.cta1':         'Commencer — 3 analyses incluses',
      'hero.cta2':         'Voir le processus',

      /* Stats */
      'stat.defects':      'Types de défauts reconnus',
      'stat.time':         'Temps de génération du rapport',
      'stat.widths':       'Catégories de largeur de fissure',
      'stat.sections':     'Sections du rapport par analyse',

      /* Features */
      'feat.label':        'Fonctionnalités',
      'feat.heading':      'Tout ce qu\'il faut pour la pathologie du béton',
      'feat1.title':       'Détection multi-défauts',
      'feat1.desc':        'Identifie les fissures, éclatements, délaminations, carbonatation, corrosion des armatures, efflorescence, faïençage RAG et vides à partir d\'une seule photographie.',
      'feat2.title':       'Rapports d\'ingénierie en 8 sections',
      'feat2.desc':        'Rapports structurés couvrant la classification des défauts, les observations visuelles, l\'analyse des causes, l\'évaluation de la sévérité, le risque structurel, la stratégie de réparation et la cotation d\'état.',
      'feat3.title':       'Analyse contextuelle',
      'feat3.desc':        'Un questionnaire de 7 champs alimente l\'IA — type d\'élément, conditions d\'exposition, âge de la structure, réparations antérieures, infiltrations d\'eau — pour des évaluations beaucoup plus précises.',
      'feat4.title':       'Carte des défauts IA codée par couleur',
      'feat4.desc':        'Notre IA de vision trace un calque précis directement sur votre photo. Les fissures sont codées par largeur mesurée : cyan (capillaire <0,5 mm), jaune (moyen 0,5–2 mm), orange (large >2 mm), magenta pour les zones d\'éclatement.',
      'feat5.title':       'Export PDF en un clic',
      'feat5.desc':        'Téléchargez un PDF complet incluant les images originale et annotée, le rapport structuré en 8 sections et un avertissement professionnel — prêt à partager avec vos clients.',
      'feat6.title':       'Interface adaptée au terrain',
      'feat6.desc':        'Fonctionne sur tout appareil. Téléchargez directement depuis votre téléphone sur site et obtenez un rapport complet avant de partir. Aucune installation, aucun plugin — juste un navigateur.',

      /* How it works */
      'how.label':         'Processus',
      'how.heading':       'De la photo de terrain au rapport d\'ingénierie',
      'how.step1.title':   'Téléchargez la photo de chantier',
      'how.step1.desc':    'Glissez-déposez ou cliquez pour télécharger une photo d\'une surface en béton. JPEG, PNG et WebP jusqu\'à 10 Mo.',
      'how.step2.title':   'Remplissez le questionnaire de site',
      'how.step2.desc':    'Répondez à 7 questions rapides — type d\'élément, âge, conditions d\'exposition, infiltration d\'eau, réparations antérieures. Le contexte améliore considérablement la précision.',
      'how.step3.title':   'L\'IA produit le rapport d\'ingénierie',
      'how.step3.desc':    'Notre IA analyse conjointement l\'image et le questionnaire, produisant un rapport de pathologie structuré en 8 sections avec classification des défauts, analyse des causes et stratégie de réparation.',
      'how.step4.title':   'L\'IA peint la carte des défauts codée',
      'how.step4.desc':    'La photo originale est traitée par notre moteur de vision, qui trace chaque fissure et remplit chaque zone d\'éclatement avec des calques codés par couleur selon la largeur mesurée.',

      /* Classification */
      'cl.label':          'Classification des défauts',
      'cl.heading':        'Codé par couleur selon la largeur de fissure',
      'cl.desc':           'Chaque fissure est classifiée visuellement selon sa largeur mesurée. Le calque utilise quatre couleurs distinctes pour que la sévérité soit lisible instantanément sur le terrain.',
      'cl.color':          'COULEUR',
      'cl.cat':            'CATÉGORIE',
      'cl.width':          'SEUIL DE LARGEUR',
      'cl.cause':          'CAUSE TYPIQUE',
      'cl.hair':           'Capillaire / Fine',
      'cl.med':            'Fissure moyenne',
      'cl.wide':           'Fissure large',
      'cl.spal':           'Zone d\'éclatement',
      'cl.cause1':         'Retrait, mouvement thermique, contrainte précoce',
      'cl.cause2':         'Surcharge structurelle, RAG, carbonatation',
      'cl.cause3':         'Surcharge, corrosion des armatures, détresse structurelle',
      'cl.cause4':         'Délamination, dommages gel-dégel, pression de corrosion',
      'cl.note':           'La classification des largeurs est réalisée visuellement par notre moteur IA. Tous les résultats doivent être vérifiés sur site par un ingénieur structurel agréé. Cet outil ne remplace pas une inspection professionnelle.',

      /* Testimonials */
      'trust.label':       'Utilisé par des professionnels',
      'trust.heading':     'Ce que disent les ingénieurs de terrain',

      /* Analyzer section */
      'az.label':          'Analyse en direct',
      'az.heading':        'Inspectez une surface en béton maintenant',
      'az.desc':           'Téléchargez une photo d\'une surface en béton, remplissez le questionnaire de site et recevez un rapport de pathologie structuré et une carte des défauts en moins d\'une minute.',
      'gate.title':        'Connectez-vous pour lancer une analyse',
      'gate.desc':         'Créez un compte gratuit et obtenez <strong>3 analyses incluses</strong> — aucune carte de crédit requise.',
      'gate.btn':          'Se connecter / Créer un compte',
      'gate.f1':           '✓ Carte des défauts codée par couleur',
      'gate.f2':           '✓ Rapport d\'ingénierie en 8 sections',
      'gate.f3':           '✓ Export PDF',

      /* CTA section */
      'cta.label':         'Commencer',
      'cta.heading':       'Accélérez vos évaluations de terrain',
      'cta.desc':          'Téléchargez une photo et obtenez un rapport de pathologie structuré en moins de 60 secondes.',
      'cta.btn1':          'Commencer l\'analyse gratuite',
      'cta.btn2':          'Nous contacter',

      /* Footer */
      'foot.product':      'Produit',
      'foot.method':       'Méthodologie',
      'foot.company':      'Entreprise',
      'foot.contact':      'Contact',
      'foot.privacy':      'Politique de confidentialité',
      'foot.terms':        'Conditions d\'utilisation',
      'foot.copy':         '© 2026 Concrete Defect AI. Tous droits réservés.',
      'foot.tag':          'Assisté par IA · Pas un rapport d\'ingénierie certifié',

      /* Login page */
      'login.tab.in':      'Se connecter',
      'login.tab.reg':     'Créer un compte',
      'login.email':       'Adresse courriel',
      'login.email.ph':    'vous@exemple.com',
      'login.pass':        'Mot de passe',
      'login.pass.ph':     'Min. 6 caractères',
      'login.pass2':       'Confirmer le mot de passe',
      'login.pass2.ph':    'Répéter votre mot de passe',
      'login.country':     'Pays',
      'login.country.ph':  'Sélectionner le pays…',
      'login.phone':       'Numéro de téléphone',
      'login.phone.ph':    '+1 555 000 0000',
      'login.privacy.lbl': 'J\'ai lu et j\'accepte la <a href="/privacy" target="_blank" style="color:var(--accent-2);">Politique de confidentialité</a> — y compris la collecte de mon courriel, pays et numéro de téléphone.',
      'login.terms.lbl':   'J\'ai lu et j\'accepte les <a href="/terms" target="_blank" style="color:var(--accent-2);">Conditions d\'utilisation</a> — y compris que les sorties IA ne sont pas des documents d\'ingénierie certifiés.',
      'login.btn.in':      'Se connecter',
      'login.btn.reg':     'Créer un compte',
      'login.foot.new':    'Nouveau ? <a href="#" onclick="switchTab(\'register\');return false;" style="color:var(--accent-2);">Créez un compte gratuit</a> — inclut 3 analyses.',
      'login.foot.have':   'Vous avez déjà un compte ? <a href="#" onclick="switchTab(\'login\');return false;" style="color:var(--accent-2);">Se connecter</a>',
      'login.headline':    'Inspection professionnelle du béton, propulsée par <em>l\'IA</em>',
      'login.sub':         'Téléchargez une photo et recevez un rapport de pathologie structuré en 8 sections avec une carte des défauts codée par couleur — en moins de 60 secondes.',
      'login.perk1':       '3 analyses gratuites incluses avec chaque compte',
      'login.perk2':       'Carte des fissures codée par sévérité',
      'login.perk3':       'Analyse des causes et stratégie de réparation',
      'login.perk4':       'Export PDF en un clic',
      'login.perk5':       'Aucune carte de crédit requise',

      /* App page */
      'app.tool':          'Outil d\'analyse',
      'app.heading':       'Analyse des défauts du béton',
      'app.sub':           'Téléchargez une photo de chantier, remplissez le contexte du site et recevez votre rapport en moins de 60 secondes.',
      'app.signout':       'Se déconnecter',
      'app.delete':        'Supprimer le compte',
      'app.upload.lbl':    'Cliquez pour télécharger ou glisser-déposer',
      'app.upload.hint':   'JPEG, PNG, WebP — Max 10 Mo',
      'app.q.title':       'Questionnaire de contexte du site',
      'app.q.desc':        'Le contexte améliore considérablement la précision du rapport — 30 secondes suffisent.',
      'app.q.element':     'Type d\'élément',
      'app.q.age':         'Âge approximatif',
      'app.q.age.ph':      'ex. 25 ans',
      'app.q.exposure':    'Conditions d\'exposition',
      'app.q.water':       'Infiltration d\'eau visible ?',
      'app.q.evolving':    'Le défaut évolue-t-il ?',
      'app.q.repair':      'Réparation antérieure tentée ?',
      'app.q.notes':       'Notes de l\'inspecteur',
      'app.q.notes.ph':    'Observations : date d\'apparition, taches de rouille, fuites, historique des charges, vibrations…',
      'app.submit':        'Générer le rapport et la carte',
      'app.step1':         'Analyse de l\'image',
      'app.step2':         'Cartographie des défauts',
      'app.step3':         'Rapport prêt',
      'app.photo.lbl':     'PHOTO TÉLÉCHARGÉE',
      'app.map.lbl':       'CARTE DES DÉFAUTS IA',
      'app.pdf':           '⬇ Télécharger PDF',
      'app.report.lbl':    'Rapport d\'évaluation IA',
      'app.annot.note':    'Calque généré par IA. Doit être vérifié sur site par un ingénieur structurel agréé.',
      'app.tries':         (n) => n + (n <= 1 ? ' analyse restante' : ' analyses restantes'),
    }
  };

  /* ── Core engine ─────────────────────────────────────── */
  function getLang() {
    return localStorage.getItem('cda_lang') || 'en';
  }

  function applyLang(lang) {
    document.body.classList.remove('lang-en', 'lang-fr');
    document.body.classList.add('lang-' + lang);
    localStorage.setItem('cda_lang', lang);

    const dict = T[lang] || T['en'];

    /* text content */
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (dict[key] !== undefined) el.textContent = dict[key];
    });

    /* innerHTML (allows HTML tags like <em>, <a>) */
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
      const key = el.getAttribute('data-i18n-html');
      if (dict[key] !== undefined) el.innerHTML = dict[key];
    });

    /* placeholders */
    document.querySelectorAll('[data-i18n-ph]').forEach(el => {
      const key = el.getAttribute('data-i18n-ph');
      if (dict[key] !== undefined) el.placeholder = dict[key];
    });

    /* toggle buttons */
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === lang);
    });
  }

  /* ── Public API ──────────────────────────────────────── */
  window.i18n = {
    t:   (key) => { const d = T[getLang()]; return d[key] || T['en'][key] || key; },
    set: (lang) => applyLang(lang),
    get: getLang,
  };

  /* Apply on load */
  document.addEventListener('DOMContentLoaded', () => applyLang(getLang()));
})();
