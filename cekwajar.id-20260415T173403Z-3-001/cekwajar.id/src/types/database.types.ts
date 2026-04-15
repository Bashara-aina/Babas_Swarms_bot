// ══════════════════════════════════════════════════════════════════════════════
// cekwajar.id — Database Types (auto-generated from schema)
// ══════════════════════════════════════════════════════════════════════════════

export type SubscriptionTier = 'free' | 'basic' | 'pro'
export type BillingPeriod = 'monthly' | 'annual'
export type TransactionStatus = 'pending' | 'settlement' | 'capture' | 'expire' | 'cancel' | 'deny' | 'refund'
export type OCRSource = 'google_vision' | 'tesseract' | 'manual'
export type PayslipVerdict = 'SESUAI' | 'ADA_PELANGGARAN'
export type ExperienceBucket = '0-2' | '3-5' | '6-10' | '10+'
export type PropertyType = 'RUMAH' | 'TANAH' | 'APARTEMEN' | 'RUKO'
export type PropertySource = '99co' | 'rumah123' | 'olx' | 'user_submission'
export type BPJSComponent = 'JHT' | 'JP' | 'JKK' | 'JKM' | 'KESEHATAN'
export type BPJSParty = 'employee' | 'employer'
export type TERCategory = 'A' | 'B' | 'C'

export interface Database {
  public: {
    Tables: {
      user_profiles: {
        Row: {
          id: string
          email: string
          full_name: string | null
          subscription_tier: SubscriptionTier
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          email: string
          full_name?: string | null
          subscription_tier?: SubscriptionTier
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          email?: string
          full_name?: string | null
          subscription_tier?: SubscriptionTier
          created_at?: string
          updated_at?: string
        }
      }
      subscriptions: {
        Row: {
          id: string
          user_id: string | null
          plan_type: 'basic' | 'pro'
          status: 'active' | 'expired' | 'cancelled'
          starts_at: string
          ends_at: string
          last_payment_order_id: string | null
          created_at: string | null
        }
        Insert: {
          id?: string
          user_id?: string | null
          plan_type: 'basic' | 'pro'
          status?: 'active' | 'expired' | 'cancelled'
          starts_at?: string
          ends_at: string
          last_payment_order_id?: string | null
          created_at?: string | null
        }
        Update: {
          id?: string
          user_id?: string | null
          plan_type?: 'basic' | 'pro'
          status?: 'active' | 'expired' | 'cancelled'
          starts_at?: string
          ends_at?: string
          last_payment_order_id?: string | null
          created_at?: string | null
        }
      }
      transactions: {
        Row: {
          id: string
          user_id: string | null
          midtrans_order_id: string
          plan_type: string
          billing_period: BillingPeriod
          gross_amount: number
          status: TransactionStatus
          fraud_status: string | null
          midtrans_payload: Record<string, unknown> | null
          is_webhook_processed: boolean
          webhook_received_at: string | null
          created_at: string | null
        }
        Insert: {
          id?: string
          user_id?: string | null
          midtrans_order_id: string
          plan_type: string
          billing_period: BillingPeriod
          gross_amount: number
          status?: TransactionStatus
          fraud_status?: string | null
          midtrans_payload?: Record<string, unknown> | null
          is_webhook_processed?: boolean
          webhook_received_at?: string | null
          created_at?: string | null
        }
        Update: {
          id?: string
          user_id?: string | null
          midtrans_order_id?: string
          plan_type?: string
          billing_period?: BillingPeriod
          gross_amount?: number
          status?: TransactionStatus
          fraud_status?: string | null
          midtrans_payload?: Record<string, unknown> | null
          is_webhook_processed?: boolean
          webhook_received_at?: string | null
          created_at?: string | null
        }
      }
      payslip_audits: {
        Row: {
          id: string
          user_id: string | null
          session_id: string | null
          created_at: string
          delete_at: string
          gross_salary: number
          ptkp_status: string
          city: string
          month_number: number
          year: number
          has_npwp: boolean
          reported_pph21: number
          reported_jht_employee: number
          reported_jp_employee: number
          reported_jkk: number
          reported_jkm: number
          reported_kesehatan_employee: number
          reported_take_home: number
          ocr_source: OCRSource | null
          ocr_confidence: number | null
          payslip_file_path: string | null
          calculated_pph21: number | null
          calculated_jht: number | null
          calculated_jp: number | null
          calculated_kesehatan: number | null
          city_umk: number | null
          violations: Violation[]
          verdict: PayslipVerdict | null
          is_paid_result: boolean
          subscription_tier_at_time: SubscriptionTier
        }
        Insert: {
          id?: string
          user_id?: string | null
          session_id?: string | null
          created_at?: string
          delete_at?: string
          gross_salary: number
          ptkp_status: string
          city: string
          month_number: number
          year?: number
          has_npwp?: boolean
          reported_pph21?: number
          reported_jht_employee?: number
          reported_jp_employee?: number
          reported_jkk?: number
          reported_jkm?: number
          reported_kesehatan_employee?: number
          reported_take_home?: number
          ocr_source?: OCRSource | null
          ocr_confidence?: number | null
          payslip_file_path?: string | null
          calculated_pph21?: number | null
          calculated_jht?: number | null
          calculated_jp?: number | null
          calculated_kesehatan?: number | null
          city_umk?: number | null
          violations?: Violation[]
          verdict?: PayslipVerdict | null
          is_paid_result?: boolean
          subscription_tier_at_time?: SubscriptionTier
        }
        Update: {
          id?: string
          user_id?: string | null
          session_id?: string | null
          created_at?: string
          delete_at?: string
          gross_salary?: number
          ptkp_status?: string
          city?: string
          month_number?: number
          year?: number
          has_npwp?: boolean
          reported_pph21?: number
          reported_jht_employee?: number
          reported_jp_employee?: number
          reported_jkk?: number
          reported_jkm?: number
          reported_kesehatan_employee?: number
          reported_take_home?: number
          ocr_source?: OCRSource | null
          ocr_confidence?: number | null
          payslip_file_path?: string | null
          calculated_pph21?: number | null
          calculated_jht?: number | null
          calculated_jp?: number | null
          calculated_kesehatan?: number | null
          city_umk?: number | null
          violations?: Violation[]
          verdict?: PayslipVerdict | null
          is_paid_result?: boolean
          subscription_tier_at_time?: SubscriptionTier
        }
      }
      ocr_quota_counter: {
        Row: {
          month_key: string
          count: number
          updated_at: string
        }
        Insert: {
          month_key: string
          count?: number
          updated_at?: string
        }
        Update: {
          month_key?: string
          count?: number
          updated_at?: string
        }
      }
      job_categories: {
        Row: {
          id: string
          title: string
          title_normalized: string
          industry: string | null
          is_active: boolean
          created_at: string | null
        }
        Insert: {
          id?: string
          title: string
          title_normalized: string
          industry?: string | null
          is_active?: boolean
          created_at?: string | null
        }
        Update: {
          id?: string
          title?: string
          title_normalized?: string
          industry?: string | null
          is_active?: boolean
          created_at?: string | null
        }
      }
      salary_submissions: {
        Row: {
          id: string
          job_category_id: string | null
          job_title_raw: string
          city: string
          province: string
          gross_salary: number
          experience_bucket: ExperienceBucket
          industry: string | null
          submission_fingerprint: string
          is_validated: boolean
          is_outlier: boolean
          submission_date: string
          created_at: string | null
        }
        Insert: {
          id?: string
          job_category_id?: string | null
          job_title_raw: string
          city: string
          province: string
          gross_salary: number
          experience_bucket: ExperienceBucket
          industry?: string | null
          submission_fingerprint: string
          is_validated?: boolean
          is_outlier?: boolean
          submission_date?: string
          created_at?: string | null
        }
        Update: {
          id?: string
          job_category_id?: string | null
          job_title_raw?: string
          city?: string
          province?: string
          gross_salary?: number
          experience_bucket?: ExperienceBucket
          industry?: string | null
          submission_fingerprint?: string
          is_validated?: boolean
          is_outlier?: boolean
          submission_date?: string
          created_at?: string | null
        }
      }
      salary_benchmarks: {
        Row: {
          id: string
          job_category_id: string | null
          city: string | null
          province: string
          experience_bucket: string | null
          data_source: string
          sample_count: number
          p25: number | null
          p50: number
          p75: number | null
          updated_at: string | null
        }
        Insert: {
          id?: string
          job_category_id?: string | null
          city?: string | null
          province: string
          experience_bucket?: string | null
          data_source: string
          sample_count: number
          p25?: number | null
          p50: number
          p75?: number | null
          updated_at?: string | null
        }
        Update: {
          id?: string
          job_category_id?: string | null
          city?: string | null
          province?: string
          experience_bucket?: string | null
          data_source?: string
          sample_count?: number
          p25?: number | null
          p50?: number
          p75?: number | null
          updated_at?: string | null
        }
      }
      umk_2026: {
        Row: {
          id: string
          province: string
          city: string
          monthly_minimum_idr: number
          effective_date: string
          source_url: string | null
        }
        Insert: {
          id?: string
          province: string
          city: string
          monthly_minimum_idr: number
          effective_date: string
          source_url?: string | null
        }
        Update: {
          id?: string
          province?: string
          city?: string
          monthly_minimum_idr?: number
          effective_date?: string
          source_url?: string | null
        }
      }
      property_benchmarks: {
        Row: {
          id: string
          province: string
          city: string
          district: string
          property_type: PropertyType
          price_per_sqm: number
          land_area_sqm: number | null
          source: PropertySource
          listing_url: string | null
          is_outlier: boolean
          scraped_at: string | null
          created_at: string | null
        }
        Insert: {
          id?: string
          province: string
          city: string
          district: string
          property_type: PropertyType
          price_per_sqm: number
          land_area_sqm?: number | null
          source: PropertySource
          listing_url?: string | null
          is_outlier?: boolean
          scraped_at?: string | null
          created_at?: string | null
        }
        Update: {
          id?: string
          province?: string
          city?: string
          district?: string
          property_type?: PropertyType
          price_per_sqm?: number
          land_area_sqm?: number | null
          source?: PropertySource
          listing_url?: string | null
          is_outlier?: boolean
          scraped_at?: string | null
          created_at?: string | null
        }
      }
      property_submissions: {
        Row: {
          id: string
          province: string
          city: string
          district: string
          property_type: string
          total_price: number
          land_area_sqm: number
          price_per_sqm: number | null
          submission_fingerprint: string | null
          created_at: string | null
        }
        Insert: {
          id?: string
          province: string
          city: string
          district: string
          property_type: string
          total_price: number
          land_area_sqm: number
          price_per_sqm?: number | null
          submission_fingerprint?: string | null
          created_at?: string | null
        }
        Update: {
          id?: string
          province?: string
          city?: string
          district?: string
          property_type?: string
          total_price?: number
          land_area_sqm?: number
          price_per_sqm?: number | null
          submission_fingerprint?: string | null
          created_at?: string | null
        }
      }
      ppp_reference: {
        Row: {
          id: string
          country_code: string
          country_name: string
          currency_code: string
          currency_symbol: string
          flag_emoji: string
          ppp_factor: number | null
          ppp_year: number | null
          is_free_tier: boolean
          display_order: number | null
          fetched_at: string | null
        }
        Insert: {
          id?: string
          country_code: string
          country_name: string
          currency_code: string
          currency_symbol: string
          flag_emoji: string
          ppp_factor?: number | null
          ppp_year?: number | null
          is_free_tier?: boolean
          display_order?: number | null
          fetched_at?: string | null
        }
        Update: {
          id?: string
          country_code?: string
          country_name?: string
          currency_code?: string
          currency_symbol?: string
          flag_emoji?: string
          ppp_factor?: number | null
          ppp_year?: number | null
          is_free_tier?: boolean
          display_order?: number | null
          fetched_at?: string | null
        }
      }
      col_cities: {
        Row: {
          id: string
          country_code: string
          city_name: string
          meal_cheap_idr: number | null
          meal_restaurant_idr: number | null
          transport_monthly_idr: number | null
          rent_1br_center_idr: number | null
          rent_1br_outside_idr: number | null
          utilities_basic_idr: number | null
          data_source: string | null
          fetched_at: string | null
        }
        Insert: {
          id?: string
          country_code: string
          city_name: string
          meal_cheap_idr?: number | null
          meal_restaurant_idr?: number | null
          transport_monthly_idr?: number | null
          rent_1br_center_idr?: number | null
          rent_1br_outside_idr?: number | null
          utilities_basic_idr?: number | null
          data_source?: string | null
          fetched_at?: string | null
        }
        Update: {
          id?: string
          country_code?: string
          city_name?: string
          meal_cheap_idr?: number | null
          meal_restaurant_idr?: number | null
          transport_monthly_idr?: number | null
          rent_1br_center_idr?: number | null
          rent_1br_outside_idr?: number | null
          utilities_basic_idr?: number | null
          data_source?: string | null
          fetched_at?: string | null
        }
      }
      abroad_salary_benchmarks: {
        Row: {
          id: string
          country_code: string
          job_title: string
          currency_code: string
          p25: number | null
          p50: number
          p75: number | null
          sample_count: number | null
          data_source: string | null
          updated_at: string | null
        }
        Insert: {
          id?: string
          country_code: string
          job_title: string
          currency_code: string
          p25?: number | null
          p50: number
          p75?: number | null
          sample_count?: number | null
          data_source?: string | null
          updated_at?: string | null
        }
        Update: {
          id?: string
          country_code?: string
          job_title?: string
          currency_code?: string
          p25?: number | null
          p50?: number
          p75?: number | null
          sample_count?: number | null
          data_source?: string | null
          updated_at?: string | null
        }
      }
      col_indices: {
        Row: {
          id: string
          city_code: string
          city_name: string
          province: string
          col_index: number
          data_year: number
          data_quarter: number
          source: string | null
          updated_at: string | null
        }
        Insert: {
          id?: string
          city_code: string
          city_name: string
          province: string
          col_index: number
          data_year: number
          data_quarter: number
          source?: string | null
          updated_at?: string | null
        }
        Update: {
          id?: string
          city_code?: string
          city_name?: string
          province?: string
          col_index?: number
          data_year?: number
          data_quarter?: number
          source?: string | null
          updated_at?: string | null
        }
      }
      col_categories: {
        Row: {
          id: string
          category_code: string
          label_id: string
          hemat_weight: number
          standar_weight: number
          nyaman_weight: number
        }
        Insert: {
          id?: string
          category_code: string
          label_id: string
          hemat_weight: number
          standar_weight: number
          nyaman_weight: number
        }
        Update: {
          id?: string
          category_code?: string
          label_id?: string
          hemat_weight?: number
          standar_weight?: number
          nyaman_weight?: number
        }
      }
      pph21_ter_rates: {
        Row: {
          id: string
          category: TERCategory
          min_salary: number
          max_salary: number
          monthly_rate_percent: number
          effective_from: string
        }
        Insert: {
          id?: string
          category: TERCategory
          min_salary: number
          max_salary: number
          monthly_rate_percent: number
          effective_from?: string
        }
        Update: {
          id?: string
          category?: TERCategory
          min_salary?: number
          max_salary?: number
          monthly_rate_percent?: number
          effective_from?: string
        }
      }
      bpjs_rates: {
        Row: {
          id: string
          component: BPJSComponent
          party: BPJSParty
          rate_percent: number
          salary_cap_idr: number | null
          notes: string | null
          effective_from: string
        }
        Insert: {
          id?: string
          component: BPJSComponent
          party: BPJSParty
          rate_percent: number
          salary_cap_idr?: number | null
          notes?: string | null
          effective_from?: string
        }
        Update: {
          id?: string
          component?: BPJSComponent
          party?: BPJSParty
          rate_percent?: number
          salary_cap_idr?: number | null
          notes?: string | null
          effective_from?: string
        }
      }
      ptkp_values: {
        Row: {
          id: string
          status_code: string
          description: string
          annual_value_idr: number
          effective_from: string
        }
        Insert: {
          id?: string
          status_code: string
          description: string
          annual_value_idr: number
          effective_from: string
        }
        Update: {
          id?: string
          status_code?: string
          description?: string
          annual_value_idr?: number
          effective_from?: string
        }
      }
      user_consents: {
        Row: {
          id: string
          user_id: string | null
          policy_version: string
          privacy_policy_accepted: boolean
          terms_accepted: boolean
          marketing_accepted: boolean
          accepted_at: string
          ip_hash: string | null
        }
        Insert: {
          id?: string
          user_id?: string | null
          policy_version: string
          privacy_policy_accepted?: boolean
          terms_accepted?: boolean
          marketing_accepted?: boolean
          accepted_at?: string
          ip_hash?: string | null
        }
        Update: {
          id?: string
          user_id?: string | null
          policy_version?: string
          privacy_policy_accepted?: boolean
          terms_accepted?: boolean
          marketing_accepted?: boolean
          accepted_at?: string
          ip_hash?: string | null
        }
      }
    }
    Views: {}
    Functions: {
      increment_ocr_counter: {
        Args: Record<string, never>
        Returns: number
      }
    }
    Enums: {}
  }
}

// ─── Violation type used in payslip_audits ───────────────────────────────────

export type ViolationCode = 'V01' | 'V02' | 'V03' | 'V04' | 'V05' | 'V06' | 'V07'
export type ViolationSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'

export interface Violation {
  code: ViolationCode
  severity: ViolationSeverity
  titleID: string
  descriptionID: string
  differenceIDR: number
  actionID: string
}
