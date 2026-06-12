export const FLAGS = {
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

export function flag(team) {
  return FLAGS[team] ?? '🏳️'
}
