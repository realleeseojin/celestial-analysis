import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time


# ============================================================
# 1. SEDS Messier Catalog 스크래핑
# ============================================================

def scrape_seds_messier():
    """
    SEDS 웹사이트에서 Messier 천체 목록 수집
    http://www.messier.seds.org/dataRA.html
    """
    url = "http://www.messier.seds.org/dataRA.html"
    
    print("=" * 60)
    print("🔭 SEDS Messier Catalog 수집 시작")
    print(f"📡 URL: {url}")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # BeautifulSoup 파싱
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # <pre> 태그 안의 데이터 추출
        pre_tag = soup.find('pre')
        
        if pre_tag:
            raw_text = pre_tag.get_text()
            return parse_seds_data(raw_text)
        else:
            print("⚠️ 데이터를 찾을 수 없습니다.")
            return None
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None


def parse_seds_data(raw_text):
    """SEDS 데이터 파싱"""
    
    # 천체 종류 코드 매핑
    type_mapping = {
        '1': 'Open Cluster',       # 산개성단
        '2': 'Globular Cluster',   # 구상성단
        '3': 'Planetary Nebula',   # 행성상 성운
        '4': 'Diffuse Nebula',     # 발광/반사 성운
        '5': 'Spiral Galaxy',      # 나선 은하
        '6': 'Elliptical Galaxy',  # 타원 은하
        '7': 'Irregular Galaxy',   # 불규칙 은하
        '8': 'Lenticular Galaxy',  # 렌즈형 은하
        '9': 'Supernova Remnant',  # 초신성 잔해
        'A': 'Asterism',           # 성군
        'B': 'Milky Way Patch',    # 은하수 영역
        'C': 'Binary Star'         # 이중성
    }
    
    # 대분류 매핑
    category_mapping = {
        'Open Cluster': '성단', 'Globular Cluster': '성단',
        'Planetary Nebula': '성운', 'Diffuse Nebula': '성운', 'Supernova Remnant': '성운',
        'Spiral Galaxy': '은하', 'Elliptical Galaxy': '은하', 
        'Irregular Galaxy': '은하', 'Lenticular Galaxy': '은하',
        'Asterism': '기타', 'Milky Way Patch': '기타', 'Binary Star': '기타'
    }
    
    objects = []
    lines = raw_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or not line.startswith('M'):
            continue
        
        parts = line.split()
        if len(parts) < 11:
            continue
            
        try:
            m_number = parts[0]
            ngc_number = parts[1]
            constellation = parts[2]
            type_code = parts[3]
            
            # RA (적경)
            ra_h, ra_m = parts[4], parts[5]
            ra_decimal = float(ra_h) + float(ra_m) / 60
            
            # Dec (적위)
            dec_d, dec_m = parts[6], parts[7]
            dec_val = dec_d.replace('+', '')
            dec_sign = -1 if '-' in dec_d else 1
            dec_decimal = dec_sign * (abs(float(dec_val)) + float(dec_m) / 60)
            
            # 밝기, 크기, 거리
            magnitude = float(parts[8])
            size = parts[9]
            distance = parts[10] if len(parts) > 10 else None
            
            obj_type = type_mapping.get(type_code, 'Unknown')
            category = category_mapping.get(obj_type, '기타')
            
            objects.append({
                'messier': m_number,
                'ngc': ngc_number,
                'constellation': constellation,
                'type_code': type_code,
                'object_type': obj_type,
                'category': category,
                'ra_h': float(ra_h),
                'ra_m': float(ra_m),
                'ra_decimal': round(ra_decimal, 4),
                'dec_d': float(dec_val) * dec_sign,
                'dec_m': float(dec_m),
                'dec_decimal': round(dec_decimal, 4),
                'magnitude': magnitude,
                'size': size,
                'distance_kly': distance
            })
            
        except (ValueError, IndexError):
            continue
    
    print(f"✅ {len(objects)}개 천체 수집 완료")
    return pd.DataFrame(objects)


# ============================================================
# 2. Wikipedia Messier Objects 스크래핑
# ============================================================

def scrape_wikipedia_messier():
    """
    Wikipedia에서 Messier 천체 목록 수집
    https://en.wikipedia.org/wiki/List_of_Messier_objects
    """
    url = "https://en.wikipedia.org/wiki/List_of_Messier_objects"
    
    print("\n" + "=" * 60)
    print("📚 Wikipedia Messier 목록 수집 시작")
    print(f"📡 URL: {url}")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # wikitable 클래스 테이블 찾기
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) > 100:  # Messier 목록 테이블 (110개 + 헤더)
                return parse_wikipedia_table(table)
        
        print("⚠️ 적절한 테이블을 찾지 못했습니다.")
        return None
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None


def parse_wikipedia_table(table):
    """Wikipedia 테이블 파싱"""
    
    rows = table.find_all('tr')
    objects = []
    
    for row in rows[1:]:  # 헤더 제외
        cells = row.find_all(['td', 'th'])
        
        if len(cells) >= 8:
            try:
                # 각 셀에서 텍스트 추출
                messier = cells[0].get_text(strip=True)
                ngc = cells[1].get_text(strip=True)
                common_name = cells[2].get_text(strip=True)
                obj_type = cells[3].get_text(strip=True)
                distance_ly = cells[4].get_text(strip=True)
                constellation = cells[5].get_text(strip=True)
                magnitude = cells[6].get_text(strip=True)
                
                # 이미지 셀이 있는 경우
                if len(cells) >= 9:
                    ra = cells[7].get_text(strip=True)
                    dec = cells[8].get_text(strip=True)
                else:
                    ra, dec = '', ''
                
                objects.append({
                    'messier': messier,
                    'ngc': ngc,
                    'common_name': common_name,
                    'object_type': obj_type,
                    'distance': distance_ly,
                    'constellation': constellation,
                    'magnitude': magnitude,
                    'ra': ra,
                    'dec': dec
                })
                
            except Exception:
                continue
    
    print(f"✅ {len(objects)}개 천체 수집 완료")
    return pd.DataFrame(objects)


# ============================================================
# 3. NGC 카탈로그 스크래핑 (추가 데이터)
# ============================================================

def scrape_ngc_catalog():
    """
    Wikipedia NGC 카탈로그 일부 수집
    """
    url = "https://en.wikipedia.org/wiki/List_of_NGC_objects"
    
    print("\n" + "=" * 60)
    print("🌌 NGC Catalog 수집 시작")
    print(f"📡 URL: {url}")
    print("=" * 60)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 모든 테이블에서 NGC 데이터 추출
        tables = soup.find_all('table', {'class': 'wikitable'})
        
        all_objects = []
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 4:
                    try:
                        ngc = cells[0].get_text(strip=True)
                        obj_type = cells[1].get_text(strip=True)
                        constellation = cells[2].get_text(strip=True)
                        
                        all_objects.append({
                            'ngc': ngc,
                            'object_type': obj_type,
                            'constellation': constellation
                        })
                    except:
                        continue
        
        print(f"✅ {len(all_objects)}개 NGC 천체 수집 완료")
        return pd.DataFrame(all_objects)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return None


# ============================================================
# 4. 데이터 정제 함수
# ============================================================

def clean_data(df):
    """수집된 데이터 정제"""
    
    if df is None or df.empty:
        return None
    
    # 거리 숫자 변환
    if 'distance_kly' in df.columns:
        df['distance_kly'] = pd.to_numeric(df['distance_kly'], errors='coerce')
    
    # 크기 평균값 계산 (예: "17x10" -> 13.5)
    if 'size' in df.columns:
        def parse_size(s):
            if pd.isna(s):
                return None
            s = str(s)
            if 'x' in s.lower():
                parts = re.split(r'[xX]', s)
                try:
                    return (float(parts[0]) + float(parts[1])) / 2
                except:
                    return None
            try:
                return float(s)
            except:
                return None
        
        df['size_arcmin'] = df['size'].apply(parse_size)
    
    return df


def save_data(df, filename):
    """CSV 파일로 저장"""
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"\n💾 저장 완료: {filename}")
    print(f"   - {len(df)}개 레코드")
    print(f"   - 컬럼: {list(df.columns)}")


# ============================================================
# 5. 메인 실행
# ============================================================

def main():
    print("\n" + "🌟" * 25)
    print("  천체 관측 데이터 수집 (BeautifulSoup)")
    print("🌟" * 25 + "\n")
    
    # 1. SEDS Messier 수집
    seds_df = scrape_seds_messier()
    if seds_df is not None:
        seds_df = clean_data(seds_df)
        save_data(seds_df, 'messier_seds.csv')
    
    # 2. Wikipedia Messier 수집
    wiki_df = scrape_wikipedia_messier()
    if wiki_df is not None:
        save_data(wiki_df, 'messier_wikipedia.csv')
    
    # 3. NGC 카탈로그 수집 (선택)
    # ngc_df = scrape_ngc_catalog()
    # if ngc_df is not None:
    #     save_data(ngc_df, 'ngc_catalog.csv')
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 수집 결과 요약")
    print("=" * 60)
    
    if seds_df is not None:
        print("\n[천체 대분류별 개수]")
        print(seds_df['category'].value_counts())
        print("\n[천체 세부 종류별 개수]")
        print(seds_df['object_type'].value_counts())
        print("\n[밝기(등급) 통계]")
        print(seds_df['magnitude'].describe())
    
    return seds_df, wiki_df


if __name__ == "__main__":
    seds_data, wiki_data = main()
