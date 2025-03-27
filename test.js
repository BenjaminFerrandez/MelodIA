// Authorization token that must have been created previously. See : https://developer.spotify.com/documentation/web-api/concepts/authorization
const token = 'BQDLOL0Gb2aR4HmdYPh7ROdgR_Q41AUewPjHKps3bFEW4eEJ0sEy_v2GmXP2L82Nc_gOxY_BbKZc8Pw2fa_UFGRxpSDUQNjsbdaxsGREVrzHg3jkdV5t49QP97-GgLsvEUk_dVisnWGzj8D-_p-H4Yd_N7Q0tdp_--Ws1G2wPywvaKUS4VNuhWaMRzL8ew7pOiXHUl-TQzw1Tfoeh0cfCR3f8nDI8tw1lh1tDM30Qx5HsMEY3C0TXoOaUTryJxw_XqYixVPhJSvomKHdmWsP_dpE7HkIrpn1_nAXM2xJdcVsGkJA2rkEfW3p';
async function fetchWebApi(endpoint, method, body) {
  const res = await fetch(`https://api.spotify.com/${endpoint}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    method,
    body:JSON.stringify(body)
  });
  return await res.json();
}

async function getTopTracks(){
  // Endpoint reference : https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks
  return (await fetchWebApi(
    'v1/me/top/tracks?time_range=long_term&limit=5', 'GET'
  )).items;
}

const topTracks = await getTopTracks();
console.log(
  topTracks?.map(
    ({name, artists}) =>
      `${name} by ${artists.map(artist => artist.name).join(', ')}`
  )
);