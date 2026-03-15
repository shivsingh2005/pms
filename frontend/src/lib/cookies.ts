import Cookies from "js-cookie";

const TOKEN_KEY = "pms_token";
const REFRESH_TOKEN_KEY = "pms_refresh_token";

const isSecureContext = typeof window !== "undefined" ? window.location.protocol === "https:" : true;

export const authCookies = {
  setToken(token: string) {
    Cookies.set(TOKEN_KEY, token, {
      secure: isSecureContext,
      sameSite: "strict",
      expires: 1,
    });
  },
  getToken() {
    return Cookies.get(TOKEN_KEY);
  },
  clearToken() {
    Cookies.remove(TOKEN_KEY);
  },
  setRefreshToken(token: string) {
    Cookies.set(REFRESH_TOKEN_KEY, token, {
      secure: isSecureContext,
      sameSite: "strict",
      expires: 14,
    });
  },
  getRefreshToken() {
    return Cookies.get(REFRESH_TOKEN_KEY);
  },
  clearRefreshToken() {
    Cookies.remove(REFRESH_TOKEN_KEY);
  },
};
