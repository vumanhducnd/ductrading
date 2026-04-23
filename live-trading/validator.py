"""
Validator mã cổ phiếu Việt Nam.
Hỗ trợ sàn HOSE, HNX và UpCom.
Trích xuất mã từ comment thô và kiểm tra tính hợp lệ.
"""

import re

# ── Danh sách mã HOSE ────────────────────────────────────────────────────────
HOSE_TICKERS = {
    # Ngân hàng
    "VCB", "BID", "CTG", "TCB", "MBB", "ACB", "VPB", "HDB", "TPB", "STB",
    "EIB", "MSB", "OCB", "LPB", "SSB", "VIB", "SGB", "BAB", "KLB", "BVB",
    "NAB", "PGB", "VAB", "ABB",
    # Bảo hiểm
    "BVH", "MIG", "BMI", "VNR", "PTI", "PGI", "ABI",
    # Chứng khoán
    "SSI", "VND", "HCM", "BSI", "CTS", "AGR", "APS", "IVS", "ORS",
    "FTS", "EVS", "VCI", "TVB", "VDS", "VFS", "VIX", "TCI", "KIS",
    # Bất động sản
    "VIC", "VHM", "NVL", "PDR", "KDH", "DXG", "VRE", "BCM", "DIG", "AGG",
    "HDG", "CEO", "ITA", "QCG", "TDH", "NLG", "TDC", "SJS", "KBC", "IDC",
    "SCR", "NBB", "LDG", "HBC", "CII", "LCG", "DRH", "HAR", "KAC", "SIP",
    "VPI", "DPG", "TCH", "CRE", "NTL", "NVT", "DXS", "HPX", "TDM",
    "CCL", "IJC", "ILA", "CKG", "IPA", "DXL", "PTL", "TIG", "FDC",
    "HAG", "DIG", "HDC", "NHA",
    # Hàng tiêu dùng / Thực phẩm / Đồ uống
    "VNM", "MSN", "MWG", "PNJ", "SAB", "QNS", "MCH", "MML", "HNG", "BAF",
    "LSS", "SLS", "TLG", "KDC", "VCF", "CLC", "SBT", "BHS",
    "NSC", "NFC", "ANV", "IDI", "VHC", "ABT", "ACL", "FMC", "CMX",
    "DAG", "TAC", "PAN", "HVG", "TS4", "AAA", "AAM", "AGF", "AGM",
    "LAF", "MST",
    # Dầu khí / Năng lượng / Điện
    "GAS", "PLX", "OIL", "PVD", "PVS", "POW", "NT2", "PPC", "REE",
    "GEG", "EVG", "PGV", "BCG", "CHP", "SHP", "DNH", "KHP",
    "VSH", "SBA", "MHC", "TBC", "BSR", "PVT", "GVR", "EVE", "EVF",
    "TMP", "GHC", "NBP", "BEL",
    # Vật liệu xây dựng / Xây dựng / Hạ tầng
    "HT1", "BCC", "THG", "CTD", "FCN", "VCG", "HUT", "PC1", "PTC",
    "HHV", "C4G", "CTI", "CTR", "CVT", "C32", "C47", "C21",
    "LHG", "HUD", "LIG", "PVC", "PXS", "SC5", "VCC", "VC3", "VC9",
    "HBC", "LCG", "DIC", "PTL",
    # Hóa chất / Phân bón
    "DCM", "DPM", "LAS", "BFC", "SFG", "DDV", "TNC", "DGC", "PMC",
    # Hàng không / Logistics / Vận tải biển
    "VJC", "HVN", "GMD", "VSC", "VOS", "STG", "SFI",
    "TMS", "VTO", "VNA", "AST", "SCS", "HAH", "PVT",
    # Viễn thông / Công nghệ
    "FPT", "ITD", "DGW", "SAM", "ST8", "FRT",
    # Dệt may / May mặc
    "MSH", "TCM", "GIL", "EVE", "STK", "VNT", "VGT", "TNG",
    # Y tế / Dược phẩm
    "DHG", "IMP", "DMC", "OPC", "TRA", "DBD", "DVN", "PME", "JVC", "AMV",
    # Thép / Kim loại
    "HPG", "NKG", "HSG", "TLH", "SMC", "POM", "VGS", "TVN",
    # Cao su thiên nhiên
    "PHR", "DPR", "TPC", "HRC", "SVR",
    # Thương mại / Xuất nhập khẩu / Khác
    "PET", "VFG", "ITQ", "SAG", "RCL", "VNS", "FIT",
    "GEX", "VTP", "VTS", "VNE", "NRC", "WSB", "SVC",
    "SKG", "SKS", "SGN", "TMT", "VNL", "VPI",
}

# ── Danh sách mã HNX ─────────────────────────────────────────────────────────
HNX_TICKERS = {
    # Ngân hàng
    "SHB", "NVB",
    # Bảo hiểm
    "PVI",
    # Chứng khoán
    "SHS", "BVS", "HBS", "MBS", "TVS", "ART", "PSI", "SBS", "VIG", "WSS",
    # Bất động sản
    "TDN", "NDN", "KLF", "PVL", "HGM", "VKC", "GTC", "BII",
    "SIC", "VHH", "HLD", "SHN", "CEO", "TIG",
    # Vật liệu xây dựng / Xây dựng / Hạ tầng
    "NTP", "BMP", "VCS", "LCS", "V21", "S74", "NHA",
    "VC3", "VC9", "HUT", "C4G", "PC1", "PTC", "VCG", "VCC",
    # Công nghệ / Viễn thông
    "CMG", "SGT", "ELC", "VTC",
    # Dệt may
    "TNG", "VGT", "STK", "TTB",
    # Hàng tiêu dùng
    "HHC", "CAN", "VDL", "MEC", "THT",
    # Thép / Kim loại
    "NHH", "VIS", "KMT", "BTS",
    # Nông nghiệp / Thực phẩm
    "BAX", "VIF", "SJ1", "BAS", "HNF",
    # Vận tải / Logistics
    "VGP", "MVN", "SFI", "HAH", "VNS",
    # Y tế
    "DBD", "AMV",
    # Năng lượng
    "SBA", "VSH", "TBC",
    # Khai khoáng
    "DHM", "KSB", "BMF",
    # Khác
    "DTD", "HTP", "PLC", "PMP", "TV2", "VIT", "VKD",
    "GLT", "GLS", "DAP", "DAV", "DCS", "DL1",
    "TDT", "NDX", "HBH", "BKS", "BKH", "ACE", "ACT",
    "HMB", "HAP", "LNC", "LNT", "MAC", "MAD", "MAP",
    "MCC", "MCI", "MCL", "MCO", "MCS", "MDN",
    "NBC", "NBT", "NDM", "NET", "NLC", "NLS", "NNT",
    "PPH", "PSC", "PTC", "PTD", "PTE", "PTG", "PTS",
    "QHD", "QHG", "QHT", "QNC", "QNI", "QPN", "QST", "QTC",
    "SFC", "SGM", "SMT", "SMS",
    "TAR", "TBD", "TCJ", "TGG", "THI", "TKC",
    "VCC", "VBH", "VID", "VMB",
}

# ── Danh sách mã UpCom ───────────────────────────────────────────────────────
UPCOM_TICKERS = {
    # Ngân hàng / Tài chính
    "ABB", "BDB", "NCB", "PGD", "VBB", "OBC", "PAB", "SCB", "UAB",
    "BAB", "NAB", "KLB", "NAV", "BSH",
    # Hàng không / Cảng / Logistics
    "ACV", "NAS", "HAN", "VGP", "MVN", "HAD",
    "NAS", "GMD", "APS", "AGS",
    # Bất động sản
    "CDC", "IDJ", "HRS", "NRC", "NDL", "VRC", "FLC", "GAB",
    "HID", "HHC", "GCB", "OCI", "SIF", "SJD",
    "TBD", "TCJ", "TGG", "VPH", "VCM", "VBC",
    # Công nghiệp / Xây dựng
    "DNC", "DSN", "HCC", "HTC", "HOM", "HPM", "HMB",
    "ICI", "LAG", "LAM", "LCI", "LCD", "LHC",
    "NDC", "NHC", "NHK", "NID", "NMC", "NNC",
    "OBC", "PBS", "PCG", "PHC", "PHN",
    "V21", "VAP", "VNC", "VPC", "VTK",
    # Năng lượng / Điện
    "CAB", "DNW", "DIN", "NBP", "TLC", "UIH",
    # Khai khoáng / Tài nguyên
    "DCS", "DHM", "DL1", "HGM", "KCD", "KHG", "NLC",
    "NDM", "NNT", "GDT", "GLS", "AGM",
    # Thực phẩm / Nông nghiệp
    "LAF", "BAS", "BAX", "HNF", "HNM", "SJ1", "VIF",
    "AAM", "ACL", "AGF", "ANL",
    # Dệt may
    "HTG", "GIL",
    # Dầu khí
    "PVA", "PVL", "PVX", "PIG", "PKG", "PLB",
    "PMD", "PMG", "PMI", "PML", "PMN", "PMV",
    # Hóa chất
    "PMC", "PMV", "DDV",
    # Thương mại / Khác
    "NAG", "NCA", "OGC", "SFC",
    "UNI", "YEG", "VID", "VKC", "VKD",
    "HLG", "HMS", "HST", "HTC",
    "IFS", "IDC",
    "TAR", "THI", "TKC",
    "WCS", "WSS",
    "MCC", "MCO", "MIM", "MED",
    "DAD", "DAP", "DAV",
    "EBC", "EBS", "ECI", "FCS",
    "OBC", "PAG", "POT",
    "SCL", "SCN", "SCR",
}

# Tra cứu nhanh: mã → sàn
_HOSE_SET = frozenset(HOSE_TICKERS)
_HNX_SET  = frozenset(HNX_TICKERS)
_UPCOM_SET = frozenset(UPCOM_TICKERS)
_ALL_TICKERS = _HOSE_SET | _HNX_SET | _UPCOM_SET

# Regex tìm chuỗi 2-5 ký tự chữ in hoa (mã cổ phiếu tiềm năng)
_TICKER_PATTERN = re.compile(r'\b([A-Z]{2,5})\b')


def normalize(text: str) -> str:
    """Chuẩn hóa chuỗi: uppercase, bỏ khoảng trắng thừa và ký tự đặc biệt."""
    text = text.upper().strip()
    text = re.sub(r'[^A-Z0-9\s]', ' ', text)
    return text


def is_valid_ticker(symbol: str) -> bool:
    """Kiểm tra mã cổ phiếu có nằm trong danh sách hợp lệ không."""
    return symbol.upper().strip() in _ALL_TICKERS


def get_exchange(symbol: str) -> str | None:
    """Trả về sàn giao dịch của mã ('HOSE', 'HNX' hoặc 'UpCom'), None nếu không hợp lệ."""
    s = symbol.upper().strip()
    if s in _HOSE_SET:
        return "HOSE"
    if s in _HNX_SET:
        return "HNX"
    if s in _UPCOM_SET:
        return "UpCom"
    return None


def extract_tickers(comment: str) -> list[str]:
    """
    Trích xuất tất cả mã cổ phiếu hợp lệ từ một đoạn comment.
    Trả về danh sách mã duy nhất theo thứ tự xuất hiện.
    """
    normalized = normalize(comment)
    candidates = _TICKER_PATTERN.findall(normalized)
    seen = set()
    result = []
    for c in candidates:
        if c not in seen and is_valid_ticker(c):
            seen.add(c)
            result.append(c)
    return result
