# 📁 حفظ هذا الملف باسم: spss_encoder_tool.py
# ثم استخدمه في كل مرة بنقرة واحدة!

"""
ملف: spss_encoder_tool.py
أداة ترميز بيانات Excel باستخدام تعريفات SPSS
استخدام: upload_files()
"""

!pip install -q pandas pyreadstat openpyxl

import pandas as pd
import pyreadstat
from google.colab import files
import io
import re
from typing import Dict, List, Optional
import datetime

class SPSSExcelEncoder:
    """أداة ترميز بيانات Excel باستخدام تعريفات SPSS"""
    
    def __init__(self):
        self.spss_file = None
        self.excel_file = None
        self.df_excel = None
        self.meta = None
        self.results = {}
    
    def upload_files_interactive(self):
        """رفع الملفات بشكل تفاعلي"""
        print("=" * 70)
        print("🔄 **أداة الترميز التلقائي - SPSS to Excel**")
        print("=" * 70)
        
        uploaded = files.upload()
        
        # البحث عن الملفات
        spss_files = []
        excel_files = []
        
        for filename in uploaded.keys():
            if filename.lower().endswith('.sav'):
                spss_files.append(filename)
            elif filename.lower().endswith(('.xlsx', '.xls')):
                excel_files.append(filename)
        
        if len(spss_files) == 0:
            print("❌ لم أجد أي ملف SPSS (.sav)")
            return False
        
        if len(excel_files) == 0:
            print("❌ لم أجد أي ملف Excel (.xlsx, .xls)")
            return False
        
        # استخدام أول ملف من كل نوع
        self.spss_file = spss_files[0]
        self.excel_file = excel_files[0]
        
        print(f"\n✅ **الملفات المرفوعة:**")
        print(f"   📁 SPSS: {self.spss_file}")
        print(f"   📁 Excel: {self.excel_file}")
        
        return True
    
    def load_spss_metadata(self):
        """تحميل تعريفات SPSS"""
        print("\n📖 **جاري تحميل تعريفات SPSS...**")
        
        try:
            _, self.meta = pyreadstat.read_sav(self.spss_file, metadataonly=True)
            
            # استخراج جميع التعريفات
            self.variable_labels = {}
            
            if hasattr(self.meta, 'column_names'):
                for i, var_name in enumerate(self.meta.column_names):
                    if i < len(self.meta.column_labels):
                        label = self.meta.column_labels[i]
                        self.variable_labels[var_name] = label
            
            print(f"✅ تم تحميل {len(self.meta.column_names)} متغير")
            return True
            
        except Exception as e:
            print(f"❌ خطأ في تحميل SPSS: {e}")
            return False
    
    def load_excel_data(self):
        """تحميل بيانات Excel"""
        print("\n📊 **جاري تحميل بيانات Excel...**")
        
        try:
            self.df_excel = pd.read_excel(io.BytesIO(files.open(self.excel_file).read()))
            print(f"✅ تم تحميل {self.df_excel.shape[0]} صف × {self.df_excel.shape[1]} عمود")
            return True
        except Exception as e:
            print(f"❌ خطأ في تحميل Excel: {e}")
            return False
    
    def get_spss_variable_info(self, var_name: str) -> Dict:
        """الحصول على معلومات متغير من SPSS"""
        info = {
            'exists': False,
            'index': None,
            'label': '',
            'value_labels': {}
        }
        
        if not hasattr(self.meta, 'column_names'):
            return info
        
        # البحث عن المتغير
        for i, name in enumerate(self.meta.column_names):
            if name == var_name:
                info['exists'] = True
                info['index'] = i
                
                # الحصول على التسمية
                if i < len(self.meta.column_labels):
                    info['label'] = self.meta.column_labels[i]
                
                # الحصول على تعريفات القيم
                if hasattr(self.meta, 'value_labels'):
                    if isinstance(self.meta.value_labels, dict):
                        # البحث في القاموس
                        for key, labels in self.meta.value_labels.items():
                            if key == var_name or (isinstance(key, int) and key == i):
                                info['value_labels'] = labels
                                break
                
                break
        
        return info
    
    def auto_match_columns(self) -> Dict[str, str]:
        """مطابقة الأعمدة تلقائياً بين Excel و SPSS"""
        matches = {}
        
        if self.df_excel is None or self.meta is None:
            return matches
        
        print("\n🔍 **جاري مطابقة الأعمدة تلقائياً...**")
        
        # أسماء الأعمدة في Excel
        excel_cols = list(self.df_excel.columns)
        
        # أسماء المتغيرات في SPSS
        spss_vars = self.meta.column_names if hasattr(self.meta, 'column_names') else []
        
        for spss_var in spss_vars:
            spss_var_lower = spss_var.lower()
            
            # البحث عن أفضل مطابقة
            best_match = None
            best_score = 0
            
            for excel_col in excel_cols:
                excel_col_lower = str(excel_col).lower()
                
                # حساب درجة المطابقة
                score = 0
                
                # مطابقة تامة
                if excel_col_lower == spss_var_lower:
                    score = 100
                # مطابقة جزئية
                elif spss_var_lower in excel_col_lower or excel_col_lower in spss_var_lower:
                    score = 80
                # كلمات مشتركة
                elif len(set(spss_var_lower.split()) & set(excel_col_lower.split())) > 0:
                    score = 60
                
                if score > best_score:
                    best_score = score
                    best_match = excel_col
            
            if best_match and best_score > 50:
                matches[spss_var] = best_match
                print(f"   ✓ {spss_var} → {best_match}")
        
        return matches
    
    def encode_variable(self, spss_var: str, excel_col: str) -> bool:
        """ترميز متغير واحد"""
        try:
            # الحصول على تعريفات القيم من SPSS
            var_info = self.get_spss_variable_info(spss_var)
            
            if not var_info['exists']:
                print(f"   ⚠️  المتغير '{spss_var}' غير موجود في SPSS")
                return False
            
            if not var_info['value_labels']:
                print(f"   ⚠️  لا توجد تعريفات قيم لـ '{spss_var}'")
                return False
            
            # إنشاء قاموس الترميز
            label_to_code = {str(label).strip(): code for code, label in var_info['value_labels'].items()}
            
            if excel_col not in self.df_excel.columns:
                print(f"   ❌ العمود '{excel_col}' غير موجود في Excel")
                return False
            
            # تنظيف البيانات
            cleaned_col = f"{excel_col}_cleaned"
            encoded_col = f"{excel_col}_encoded"
            
            # دالة تنظيف عامة
            def clean_value(val):
                if pd.isna(val):
                    return val
                
                val_str = str(val).strip()
                
                # إزالة الأرقام من البداية (مثل "1. ", "2. ")
                val_str = re.sub(r'^\d+[\.\:\)]\s*', '', val_str)
                
                # إزالة أي نص بعد "="
                if '=' in val_str:
                    val_str = val_str.split('=')[0].strip()
                
                return val_str
            
            # تطبيق التنظيف
            self.df_excel[cleaned_col] = self.df_excel[excel_col].apply(clean_value)
            
            # تطبيق الترميز
            self.df_excel[encoded_col] = self.df_excel[cleaned_col].map(label_to_code)
            
            # إحصاءات
            total = len(self.df_excel)
            encoded = self.df_excel[encoded_col].notna().sum()
            percent = encoded / total * 100 if total > 0 else 0
            
            # حفظ النتيجة
            self.results[spss_var] = {
                'excel_column': excel_col,
                'cleaned_column': cleaned_col,
                'encoded_column': encoded_col,
                'total_rows': total,
                'encoded_rows': encoded,
                'success_rate': percent,
                'labels': list(label_to_code.keys())
            }
            
            print(f"   ✅ {spss_var}: {encoded}/{total} ({percent:.1f}%)")
            return True
            
        except Exception as e:
            print(f"   ❌ خطأ في ترميز {spss_var}: {e}")
            return False
    
    def batch_encode(self, variable_mapping: Dict[str, str] = None):
        """ترميز مجموعة من المتغيرات"""
        print("\n🔄 **جاري ترميز البيانات...**")
        
        if variable_mapping is None:
            variable_mapping = self.auto_match_columns()
        
        if not variable_mapping:
            print("❌ لا توجد متغيرات للمطابقة")
            return
        
        print(f"\n📋 **عدد المتغيرات للمعالجة: {len(variable_mapping)}**")
        
        success_count = 0
        for spss_var, excel_col in variable_mapping.items():
            if self.encode_variable(spss_var, excel_col):
                success_count += 1
        
        print(f"\n✅ **النتيجة: {success_count}/{len(variable_mapping)} متغير تم ترميزه بنجاح**")
    
    def save_results(self):
        """حفظ النتائج"""
        print("\n💾 **جاري حفظ النتائج...**")
        
        if self.df_excel is None:
            print("❌ لا توجد بيانات لحفظها")
            return None
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"encoded_results_{timestamp}.xlsx"
        
        # حفظ البيانات
        self.df_excel.to_excel(output_file, index=False)
        
        # حفظ تقرير
        report_file = f"encoding_report_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("تقرير ترميز البيانات\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"ملف SPSS: {self.spss_file}\n")
            f.write(f"ملف Excel: {self.excel_file}\n")
            f.write(f"تاريخ المعالجة: {datetime.datetime.now()}\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("النتائج التفصيلية:\n")
            f.write("=" * 70 + "\n\n")
            
            for var, result in self.results.items():
                f.write(f"المتغير: {var}\n")
                f.write(f"  - العمود في Excel: {result['excel_column']}\n")
                f.write(f"  - الصفوف الكلية: {result['total_rows']}\n")
                f.write(f"  - الصفوف المرمزة: {result['encoded_rows']}\n")
                f.write(f"  - نسبة النجاح: {result['success_rate']:.1f}%\n")
                f.write(f"  - القيم المعرفة: {', '.join(result['labels'][:5])}")
                if len(result['labels']) > 5:
                    f.write(f"... ({len(result['labels'])} قيم)")
                f.write("\n\n")
        
        print(f"✅ تم حفظ البيانات في: {output_file}")
        print(f"✅ تم حفظ التقرير في: {report_file}")
        
        # تنزيل الملفات
        files.download(output_file)
        files.download(report_file)
        
        return output_file
    
    def generate_summary(self):
        """إنشاء ملخص النتائج"""
        if not self.results:
            print("❌ لا توجد نتائج لعرضها")
            return
        
        print("\n" + "=" * 70)
        print("📊 **ملخص النتائج**")
        print("=" * 70)
        
        total_vars = len(self.results)
        total_rows = next(iter(self.results.values()))['total_rows'] if self.results else 0
        
        print(f"\n📈 **الإحصائيات:**")
        print(f"   • عدد المتغيرات المرمزة: {total_vars}")
        print(f"   • عدد الصفوف: {total_rows}")
        
        print(f"\n📋 **المتغيرات المرمزة:**")
        for var, result in self.results.items():
            rate = result['success_rate']
            status = "✅" if rate > 90 else "⚠️ " if rate > 50 else "❌"
            print(f"   {status} {var}: {result['encoded_rows']}/{result['total_rows']} ({rate:.1f}%)")


# الدالة الرئيسية للاستخدام السريع
def encode_all_variables():
    """دالة سحرية - ترميز كل شيء بنقرة واحدة!"""
    encoder = SPSSExcelEncoder()
    
    # 1. رفع الملفات
    if not encoder.upload_files_interactive():
        return
    
    # 2. تحميل البيانات
    if not encoder.load_spss_metadata():
        return
    
    if not encoder.load_excel_data():
        return
    
    # 3. ترميز تلقائي
    encoder.batch_encode()
    
    # 4. حفظ النتائج
    encoder.save_results()
    
    # 5. عرض الملخص
    encoder.generate_summary()


# دالة لتشفير متغيرات محددة
def encode_specific_variables(variables_list):
    """ترميز متغيرات محددة"""
    encoder = SPSSExcelEncoder()
    
    if encoder.upload_files_interactive():
        encoder.load_spss_metadata()
        encoder.load_excel_data()
        
        # إنشاء mapping يدوي
        mapping = {}
        for spss_var in variables_list:
            # البحث عن العمود المناسب في Excel
            for excel_col in encoder.df_excel.columns:
                if spss_var.lower() in str(excel_col).lower():
                    mapping[spss_var] = excel_col
                    break
        
        encoder.batch_encode(mapping)
        encoder.save_results()
        encoder.generate_summary()


# -------------------------------------------------------------------
# 🔥 **الاستخدام السريع - اختر واحدة فقط:** 🔥
# -------------------------------------------------------------------

# الخيار 1: تشفير كل شيء تلقائياً
# encode_all_variables()

# الخيار 2: تشفير متغيرات محددة
# encode_specific_variables(['Nationality', 'Gender', 'AgeGroup', 'Education'])

# -------------------------------------------------------------------
print("\n" + "=" * 70)
print("🚀 **الأداة جاهزة!**")
print("=" * 70)
print("\n📌 **كيفية الاستخدام:**")
print("1. أزل التعليق (#) من أحد الخيارات أعلاه")
print("2. شغل الكود")
print("3. اختر ملفاتك")
print("4. انتظر النتيجة!")
print("=" * 70)