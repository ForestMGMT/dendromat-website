/**
 * Dendromat i18n — all UI strings.
 * TODO: Replace placeholder text with real translations before launch.
 *
 * Structure:
 *   t[lang].section.key = "string"
 *
 * To add a language: add a new top-level key and mirror all keys from 'de'.
 */

export const languages = {
  de: 'Deutsch',
  fr: 'Français',
  it: 'Italiano',
  en: 'English',
};

export const defaultLang = 'de';

export const t = {
  de: {
    meta: {
      title: 'Dendromat – Forstliche Werkzeuge',
      description: 'Dendromat – digitale Werkzeuge für den Schweizer Forstbereich.',
    },
    nav: {
      home: 'Start',
      tools: 'Werkzeuge',
      timelapse: 'Timelapse Creator',
      baumportraets: 'Baumarten­porträts',
      geodaten: 'Geodaten Downloader',
      ressourcen: 'Ressourcen',
      about: 'Über uns',       // TODO: add /about page later
      contact: 'Kontakt',     // TODO: add /contact page later
    },
    hero: {
      tagline: 'Die Würze des Waldes',
      clickHint: 'Klick auf das Logo, um Bäume zu verstreuen!',
    },
    intro: {
      headline: 'Digitale Werkzeuge für den Wald',
      p1: 'Dendromat versammelt digitale Werk- und Spielzeuge rund um die Waldbewirtschaftung, die Forstwissenschaft und frei verfügbare Geodaten — alles an einem Ort, frei zugänglich für alle.',
      p2: 'Wissenschaft und Entdecken soll Spass machen. Ob Fachperson, Studierende oder einfach neugierig: Die Tools hier sind so gestaltet, dass der Wald ein bisschen verständlicher — und spielerischer — wird.',
      p3: 'Alle Tools sowie die gesamte Web-Architektur und die Übersetzungen wurden mithilfe von künstlicher Intelligenz erstellt und können Fehler enthalten. Korrekturen und Rückmeldungen sind herzlich willkommen.',
      disclaimer: 'Diese Website ist ein experimenteller Prototyp und wird laufend überarbeitet — es kann dadurch zu längeren Funktionsunterbrechungen kommen.',
    },
    tools: {
      sectionTitle: 'Werkzeuge',
      sectionSubtitle: 'Praktische Helfer für Forst­fachleute und Waldinteressierte.',
      openTool: 'Werkzeug öffnen',
      comingSoon: 'Demnächst verfügbar',
      timelapse: {
        title: 'Timelapse Creator',
        desc: 'Wähle ein Gebiet auf der Karte und erstelle einen animierten Zeitraffer-GIF aus historischen Schweizer Luftbildern (swisstopo SWISSIMAGE, 1926–2025).',
      },
      baumportraets: {
        title: 'Baumarten­porträts',
        // TODO: Replace with real description
        desc: 'Detaillierte Porträts heimischer Baumarten mit Bestimmungs­hilfen, Standort­ansprüchen und forstlichem Wissen.',
      },
      geodaten: {
        title: 'Geodaten Downloader',
        desc: 'Zeichne ein Gebiet auf der Karte und lade Schweizer Geodaten (swisstopo, BAFU, Kantone) als GeoTIFF oder GeoPackage herunter.',
      },
    },
    footer: {
      // TODO: Replace with real footer content
      copyright: '© 2025 Dendromat. Alle Rechte vorbehalten.',
      legal: 'Impressum',
      privacy: 'Datenschutz',
    },
  },

  fr: {
    meta: {
      title: 'Dendromat – Outils forestiers',
      description: 'Dendromat – outils numériques pour la sylviculture suisse.',
    },
    nav: {
      home: 'Accueil',
      tools: 'Outils',
      timelapse: 'Créateur Timelapse',
      baumportraets: 'Portraits d\'essences',
      geodaten: 'Téléchargeur de géodonnées',
      ressourcen: 'Ressources',
      about: 'À propos',
      contact: 'Contact',
    },
    hero: {
      tagline: 'Condiment de la forêt',
      clickHint: 'Cliquez sur le logo pour faire pousser des arbres !',
    },
    intro: {
      headline: 'Outils numériques pour la forêt',
      p1: 'Dendromat rassemble des outils numériques autour de la gestion forestière, des sciences forestières et des géodonnées librement disponibles — le tout en un seul endroit, librement accessible à toutes et à tous.',
      p2: 'La science et la découverte se doivent d\'être ludiques. Que vous soyez professionnel·le, étudiant·e ou simplement curieux·se : les outils ici sont conçus pour rendre la forêt un peu plus compréhensible — et un peu plus jouissive.',
      p3: 'Tous les outils, l\'architecture web complète et les traductions ont été réalisés à l\'aide de l\'intelligence artificielle et peuvent contenir des erreurs. Corrections et retours sont les bienvenus.',
      disclaimer: 'Ce site est un prototype expérimental en cours de développement — des interruptions prolongées sont possibles.',
    },
    tools: {
      sectionTitle: 'Outils',
      sectionSubtitle: 'Des assistants pratiques pour les professionnels et amateurs de la forêt.',
      openTool: 'Ouvrir l\'outil',
      comingSoon: 'Bientôt disponible',
      timelapse: {
        title: 'Créateur Timelapse',
        desc: 'Sélectionnez une zone sur la carte et créez un GIF animé à partir d\'images aériennes historiques suisses (swisstopo SWISSIMAGE, 1926–2025).',
      },
      baumportraets: {
        title: 'Portraits d\'essences',
        desc: 'Portraits détaillés des essences indigènes avec aides à la détermination, exigences stationnelles et savoir forestier.',
      },
      geodaten: {
        title: 'Téléchargeur de géodonnées',
        desc: 'Dessinez une zone sur la carte et téléchargez des géodonnées suisses (swisstopo, OFEV, cantons) en GeoTIFF ou GeoPackage.',
      },
    },
    footer: {
      copyright: '© 2025 Dendromat. Tous droits réservés.',
      legal: 'Mentions légales',
      privacy: 'Protection des données',
    },
  },

  it: {
    meta: {
      title: 'Dendromat – Strumenti forestali',
      description: 'Dendromat – strumenti digitali per la selvicoltura svizzera.',
    },
    nav: {
      home: 'Inizio',
      tools: 'Strumenti',
      timelapse: 'Creatore Timelapse',
      baumportraets: 'Ritratti di specie arboree',
      geodaten: 'Scaricatore di geodati',
      ressourcen: 'Risorse',
      about: 'Chi siamo',
      contact: 'Contatto',
    },
    hero: {
      tagline: 'Condimento del bosco',
      clickHint: 'Clicca sul logo per far crescere degli alberi!',
    },
    intro: {
      headline: 'Strumenti digitali per la foresta',
      p1: 'Dendromat raccoglie strumenti digitali dedicati alla gestione forestale, alle scienze forestali e ai geodati liberamente disponibili — tutto in un unico posto, liberamente accessibile a tutti.',
      p2: 'La scienza e la scoperta devono essere divertenti. Che siate professionisti, studenti o semplicemente curiosi: gli strumenti qui sono progettati per rendere la foresta un po\' più comprensibile — e un po\' più giocosa.',
      p3: 'Tutti gli strumenti, l\'intera architettura web e le traduzioni sono stati realizzati con l\'aiuto dell\'intelligenza artificiale e possono contenere errori. Correzioni e commenti sono benvenuti.',
      disclaimer: 'Questo sito è un prototipo sperimentale in continua revisione — possono verificarsi interruzioni prolungate del servizio.',
    },
    tools: {
      sectionTitle: 'Strumenti',
      sectionSubtitle: 'Assistenti pratici per i professionisti del bosco e gli appassionati.',
      openTool: 'Apri strumento',
      comingSoon: 'Disponibile presto',
      timelapse: {
        title: 'Creatore Timelapse',
        desc: 'Seleziona un\'area sulla mappa e crea una GIF animata da immagini aeree storiche svizzere (swisstopo SWISSIMAGE, 1926–2025).',
      },
      baumportraets: {
        title: 'Ritratti di specie arboree',
        desc: 'Ritratti dettagliati delle specie autoctone con aiuti per la determinazione, esigenze stazionali e conoscenze forestali.',
      },
      geodaten: {
        title: 'Scaricatore di geodati',
        desc: 'Disegna un\'area sulla mappa e scarica geodati svizzeri (swisstopo, UFAM, cantoni) in formato GeoTIFF o GeoPackage.',
      },
    },
    footer: {
      copyright: '© 2025 Dendromat. Tutti i diritti riservati.',
      legal: 'Impressum',
      privacy: 'Protezione dei dati',
    },
  },

  en: {
    meta: {
      title: 'Dendromat – Forestry Tools',
      description: 'Dendromat – digital tools for Swiss forestry professionals.',
    },
    nav: {
      home: 'Home',
      tools: 'Tools',
      timelapse: 'Timelapse Creator',
      baumportraets: 'Tree Species Portraits',
      geodaten: 'Geodata Downloader',
      ressourcen: 'Resources',
      about: 'About',
      contact: 'Contact',
    },
    hero: {
      tagline: 'The Spice of the Forest',
      clickHint: 'Click the logo to sprinkle trees!',
    },
    intro: {
      headline: 'Digital Tools for the Forest',
      p1: 'Dendromat brings together digital tools for forest management, forest science and freely available geodata — all in one place, freely accessible to everyone.',
      p2: 'Science and discovery should be fun. Whether you\'re a professional, a student or simply curious: the tools here are designed to make the forest a little more understandable — and a little more playful.',
      p3: 'All tools, the entire web architecture and the translations were created with the help of artificial intelligence and may contain errors. Corrections and feedback are warmly welcomed.',
      disclaimer: 'This website is an experimental prototype under continuous development — extended outages may occur.',
    },
    tools: {
      sectionTitle: 'Tools',
      sectionSubtitle: 'Practical helpers for forestry professionals and forest enthusiasts.',
      openTool: 'Open tool',
      comingSoon: 'Coming soon',
      timelapse: {
        title: 'Timelapse Creator',
        desc: 'Select an area on the map and generate an animated GIF from historical Swiss aerial imagery (swisstopo SWISSIMAGE, 1926–2025).',
      },
      baumportraets: {
        title: 'Tree Species Portraits',
        desc: 'Detailed portraits of native tree species with identification aids, site requirements and forestry knowledge.',
      },
      geodaten: {
        title: 'Geodata Downloader',
        desc: 'Draw an area on the map and download Swiss geodata (swisstopo, FOEN, cantons) as GeoTIFF or GeoPackage.',
      },
    },
    footer: {
      copyright: '© 2025 Dendromat. All rights reserved.',
      legal: 'Legal notice',
      privacy: 'Privacy policy',
    },
  },
};
