from django.contrib import admin
from django.contrib.auth.models import User
from core.models import Wallet, WalletTransaction, Booking

@admin.action(description="Suspend selected users")
def suspend_user(modeladmin, request, queryset):
	queryset.update(is_active=False)

@admin.action(description="Unsuspend selected users")
def unsuspend_user(modeladmin, request, queryset):
	queryset.update(is_active=True)

class UserAdmin(admin.ModelAdmin):
	list_display = ('username', 'email', 'is_active', 'is_staff', 'is_superuser')
	actions = [suspend_user, unsuspend_user]

class WalletAdmin(admin.ModelAdmin):
	list_display = ('user', 'balance')
	actions = ['add_balance']

	@admin.action(description="Add ₹1000 to selected wallets")
	def add_balance(self, request, queryset):
		for wallet in queryset:
			wallet.balance += 1000  # Example: add 1000 to selected wallets
			wallet.save()

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(WalletTransaction)




class BookingAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'vehicle_type', 'price', 'status', 'created_at')
	list_filter = ('status', 'vehicle_type')
	search_fields = ('user__username', 'pickup', 'destination')


admin.site.register(Booking, BookingAdmin)

# Customize admin site headers
admin.site.site_header = 'RideON Administration'
admin.site.site_title = 'RideON Admin'
admin.site.index_title = 'Manage RideON'
