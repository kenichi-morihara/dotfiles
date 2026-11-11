# Fixture for tests/vscode_theme/e2e.mjs: colours that need ruby-lsp semantic tokens.
class LineageService
  MAX_TABLES = 100
  attr_reader :transfer_record

  def initialize(transfer_record)
    @transfer_record = transfer_record
  end

  def executed_query = "SELECT 1"

  def run
    load!
  rescue Datamart::Error::LoadError => e
    raise e
  rescue Datamart::Error::QualityCheckViolationError => e
    raise Datamart::Error::QualityCheckViolationError.new(
      e.results,
      transfer_record: transfer_record,
      executed_query: executed_query,
    )
  end

  def input_dataset_tables
    d_tables = []
    if write_disposition_append?
      d_tables += Metadata::DataLineage::BigquerySqlParser.extract_input_dataset_tables(
        custom_variable_expanded_before_load,
      )
    end
    d_tables.uniq.first(MAX_TABLES)
  end

  def respond
    return head(:no_content) if d_tables_empty?
    redirect_to root_path and return if executed_query.empty?
    render json: { ok: true }
  end

  private

  def load! = nil
  def write_disposition_append? = true
  def custom_variable_expanded_before_load = ""
  def find_by_code(code) = find_by(code: code.upcase)
  def by_status = ->(status) { where(status:) if status.present? }
end
