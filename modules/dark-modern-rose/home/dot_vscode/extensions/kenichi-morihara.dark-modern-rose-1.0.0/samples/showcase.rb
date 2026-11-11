# frozen_string_literal: true
# rbs_inline: enabled

# Dark Modern Rose の色確認用サンプル（Rails 特有の記法 + 複雑な Ruby）
# @see https://example.com/docs
class Order < ApplicationRecord
  include Searchable, Auditable
  extend ActiveSupport::Concern

  STATUSES = %w[draft paid shipped].freeze #: Array[String]
  TAX_RATE = 0.1
  MAX_ITEMS = 1_000

  belongs_to :user, optional: true
  has_many :line_items, -> { order(:position) }, dependent: :destroy, inverse_of: :order
  has_one_attached :receipt

  enum :status, { draft: 0, paid: 1, shipped: 2 }, prefix: true
  normalizes :email, with: ->(email) { email.strip.downcase }
  delegate :name, to: :user, prefix: true, allow_nil: true
  store_accessor :meta, :note, :gift_wrap

  validates :email, presence: true, format: { with: URI::MailTo::EMAIL_REGEXP }
  validate :items_within_limit, on: :create, if: -> { line_items.any? }

  with_options if: :paid? do
    validates :paid_at, presence: true
    validates :total, numericality: { greater_than: 0 }
  end

  scope :recent, -> { where(created_at: 1.week.ago..).order(created_at: :desc) }
  scope :by_status, ->(status) { where(status:) if status.present? }

  before_validation :normalize_total
  after_commit :notify, on: %i[create update]

  class << self
    #: (String) -> Order?
    def find_by_code(code) = find_by(code: code.upcase)
  end

  def total_with_tax
    return 0 if line_items.empty?

    subtotal = line_items.sum { _1.price * _1.quantity }
    (subtotal * (1 + TAX_RATE)).round(2)
  end

  def summary
    <<~TEXT.squish
      Order ##{id} for #{user&.name || "guest"}: #{line_items.size} items
      (#{status.humanize}, #{paid? ? "paid" : "unpaid"})
    TEXT
  end

  def to_param = "#{id}-#{code.parameterize}"

  def process!(force: false, **opts, &block)
    raise ArgumentError, "already shipped" if status_shipped? && !force

    case opts
    in { mode: :fast, retries: Integer => n } if n.positive?
      n.times { |i| yield i if block_given? }
    in { mode: :slow | :safe }
      sleep 0.5
    else
      nil
    end

    transaction do
      lock!
      update!(status: :paid, paid_at: Time.current)
    end
  rescue ActiveRecord::RecordInvalid, ActiveRecord::StaleObjectError => e
    errors.add(:base, e.message) and false
  ensure
    @processing = false
  end

  def legacy_flag?
    if true
      :on
    else if false
      :off
    end
    end
  end

  private

  def items_within_limit
    errors.add(:line_items, :too_many) unless line_items.size <= MAX_ITEMS
  end

  def normalize_total
    self.total = total.to_d.round(2) unless total.nil?
  end

  def notify
    OrderMailer.with(order: self).paid.deliver_later(wait: 5.minutes)
    $stdout.puts "notified #{id}" if defined?(Rails) && Rails.env.development?
  end
end

class OrdersController < ApplicationController
  before_action :authenticate_user!
  before_action :set_order, only: %i[show update]
  helper_method :current_cart
  rescue_from ActiveRecord::RecordNotFound, with: :not_found

  def index
    @orders = Order.recent.includes(:line_items).page(params[:page])
    respond_to do |format|
      format.html
      format.json { render json: @orders }
    end
  end

  def update
    if @order.update(order_params)
      redirect_to @order, notice: t(".updated")
    else
      render :edit, status: :unprocessable_entity
    end
  end

  private

  def set_order = @order = Order.find(params[:id])

  def order_params
    params.require(:order).permit(:email, :note, line_items_attributes: %i[id quantity _destroy])
  end

  def not_found
    head :not_found and return
  end
end

class OrderSyncJob < ApplicationJob
  queue_as :default
  retry_on Timeout::Error, wait: :polynomially_longer, attempts: 3

  def perform(order_id)
    order = Order.find(order_id)
    sql = <<~SQL
      SELECT * FROM orders WHERE id = #{order.id} AND status = 'paid'
    SQL
    ActiveRecord::Base.connection.execute(sql)
  end
end

=begin
validates :ignored, presence: true
Foo::Bar.new(1) -> end
=end
