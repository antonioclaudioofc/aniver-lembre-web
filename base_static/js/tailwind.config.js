// Aniver Lembre — tokens do redesign para o Tailwind via CDN.
// Carregado em base_templates/partials/_head.html, logo depois do script do Tailwind CDN.
// Tudo está em `extend`: as classes antigas (indigo, gray...) continuam funcionando
// enquanto as telas migram para os tokens aos poucos.
tailwind.config = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        night: '#262163', // destaque do próximo aniversário, cabeçalhos de cadastro, item ativo do menu
        brand: {
          DEFAULT: '#5B5BD6', // botões primários, foco, seleção
          text: '#4B4BC8', // links e texto índigo sobre fundo claro
          hover: '#4F4FC9',
          tint: '#E4E3FB', // seleção suave, contadores
        },
        logo: '#6875F5', // apenas o símbolo
        bg: '#F6F5FB', // fundo das páginas (lavanda)
        surface: '#FFFFFF',
        field: '#FAFAFD', // fundo dos campos
        soft: '#F1F0F8', // dias marcados, botões secundários
        line: { DEFAULT: '#ECEAF5', field: '#E2E0EE' },
        ink: '#1C1B2E', // texto principal
        muted: '#67667A', // texto secundário (5,4:1 sobre bg)
        'on-night': '#C9C6F2', // texto secundário sobre night
        danger: '#B4233F',
        confetti: {
          coral: '#FF7A59',
          honey: '#FFC857',
          mint: '#3CCFAE',
          lavender: '#A9A6FF',
          'coral-light': '#FFB199', // contagem regressiva sobre night
        },
        // Tons de contato: bg (avatar), fg (letra), dot (ponto no calendário)
        contact: {
          rose: { bg: '#FCE7F3', fg: '#BE185D', dot: '#EC4899' },
          teal: { bg: '#CCFBF1', fg: '#0F766E', dot: '#14B8A6' },
          amber: { bg: '#FEF3C7', fg: '#B45309', dot: '#F59E0B' },
          violet: { bg: '#EDE9FE', fg: '#6D28D9', dot: '#8B5CF6' },
          blue: { bg: '#DBEAFE', fg: '#1D4ED8', dot: '#3B82F6' },
          lime: { bg: '#ECFCCB', fg: '#4D7C0F', dot: '#84CC16' },
          indigo: { bg: '#E0E7FF', fg: '#4338CA', dot: '#6366F1' },
          orange: { bg: '#FFEDD5', fg: '#C2410C', dot: '#F97316' },
        },
      },
      fontFamily: {
        display: ['"Bricolage Grotesque"', 'system-ui', 'sans-serif'],
        sans: ['Geist', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        hero: [
          '50px',
          { lineHeight: '1', letterSpacing: '-1.6px', fontWeight: '600' },
        ],
        page: [
          '34px',
          { lineHeight: '1.1', letterSpacing: '-1px', fontWeight: '600' },
        ],
        section: [
          '22px',
          { lineHeight: '1.2', letterSpacing: '-0.5px', fontWeight: '600' },
        ],
      },
      borderRadius: {
        field: '14px',
        day: '14px',
        block: '28px',
        modal: '28px',
      },
      boxShadow: {
        outline: '0 0 0 1px #ECEAF5',
        primary: '0 8px 20px -10px rgba(91,91,214,.9)',
        modal: '0 40px 90px -30px rgba(38,33,99,.45)',
        focus: '0 0 0 4px rgba(91,91,214,.14)',
      },
      maxWidth: { app: '1200px' },
      transitionDuration: { DEFAULT: '160ms' },
    },
  },
};
