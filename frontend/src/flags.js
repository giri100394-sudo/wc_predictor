export const EMOJI_FLAGS = {
  Algeria: '🇩🇿', Argentina: '🇦🇷', Australia: '🇦🇺', Austria: '🇦🇹',
  Belgium: '🇧🇪', 'Bosnia and Herzegovina': '🇧🇦', Brazil: '🇧🇷',
  Canada: '🇨🇦', 'Cape Verde': '🇨🇻', Colombia: '🇨🇴', 'Costa Rica': '🇨🇷',
  Croatia: '🇭🇷', 'Curaçao': '🇨🇼', 'Czech Republic': '🇨🇿', Denmark: '🇩🇰',
  'DR Congo': '🇨🇩', Ecuador: '🇪🇨', Egypt: '🇪🇬', England: '🏴',
  France: '🇫🇷', Germany: '🇩🇪', Ghana: '🇬🇭', Haiti: '🇭🇹',
  Iran: '🇮🇷', Iraq: '🇮🇶', Italy: '🇮🇹', 'Ivory Coast': '🇨🇮',
  Japan: '🇯🇵', Jordan: '🇯🇴', Mexico: '🇲🇽', Morocco: '🇲🇦',
  Netherlands: '🇳🇱', 'New Zealand': '🇳🇿', Norway: '🇳🇴', Panama: '🇵🇦',
  Paraguay: '🇵🇾', Poland: '🇵🇱', Portugal: '🇵🇹', Qatar: '🇶🇦',
  'Saudi Arabia': '🇸🇦', Scotland: '🏴', Senegal: '🇸🇳', Serbia: '🇷🇸',
  'South Africa': '🇿🇦', 'South Korea': '🇰🇷', Spain: '🇪🇸', Sweden: '🇸🇪',
  Switzerland: '🇨🇭', Tunisia: '🇹🇳', Turkey: '🇹🇷', 'United States': '🇺🇸',
  USA: '🇺🇸', Uruguay: '🇺🇾', Uzbekistan: '🇺🇿',
}

// ISO 3166-1 alpha-2 codes (flagcdn.com naming) for each World Cup team
export const ISO_CODES = {
  Algeria: 'dz', Argentina: 'ar', Australia: 'au', Austria: 'at',
  Belgium: 'be', 'Bosnia and Herzegovina': 'ba', Brazil: 'br',
  Canada: 'ca', 'Cape Verde': 'cv', Colombia: 'co', 'Costa Rica': 'cr',
  Croatia: 'hr', 'Curaçao': 'cw', 'Czech Republic': 'cz', Denmark: 'dk',
  'DR Congo': 'cd', Ecuador: 'ec', Egypt: 'eg', England: 'gb-eng',
  France: 'fr', Germany: 'de', Ghana: 'gh', Haiti: 'ht',
  Iran: 'ir', Iraq: 'iq', Italy: 'it', 'Ivory Coast': 'ci',
  Japan: 'jp', Jordan: 'jo', Mexico: 'mx', Morocco: 'ma',
  Netherlands: 'nl', 'New Zealand': 'nz', Norway: 'no', Panama: 'pa',
  Paraguay: 'py', Poland: 'pl', Portugal: 'pt', Qatar: 'qa',
  'Saudi Arabia': 'sa', Scotland: 'gb-sct', Senegal: 'sn', Serbia: 'rs',
  'South Africa': 'za', 'South Korea': 'kr', Spain: 'es', Sweden: 'se',
  Switzerland: 'ch', Tunisia: 'tn', Turkey: 'tr', 'United States': 'us',
  USA: 'us', Uruguay: 'uy', Uzbekistan: 'uz',
}

// unique team names (USA/United States collapsed to one entry)
export const TEAMS = Object.keys(ISO_CODES).filter((t) => t !== 'USA')

export function flag(team) {
  return EMOJI_FLAGS[team] ?? '🏳️'
}

export function flagUrl(team, width = 80) {
  const code = ISO_CODES[team]
  return code ? `https://flagcdn.com/w${width}/${code}.png` : null
}
