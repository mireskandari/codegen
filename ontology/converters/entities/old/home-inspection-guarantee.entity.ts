import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvChildEntity } from '@vsolv/dev-kit/nest';
import { HomeInspectionGuarantee } from '@wsphere/homes/domain';
import { WarrantyEntity } from '@wsphere/warranties/api';
import { Column, JoinColumn, ManyToOne } from 'typeorm';
import { HomeAssetEntity } from '../../home-asset';
import { HomeInspectionEntity } from '../../home-inspection/entities';
import { HomeInspectionGuaranteeAggregate } from '../models';

@VsolvChildEntity(HomeInspectionGuarantee.Type, 'tenant')
export class HomeInspectionGuaranteeEntity extends WarrantyEntity<typeof HomeInspectionGuarantee.Type> {
  @Column()
  inspectionId!: string;

  @JoinColumn({ name: 'inspectionId' })
  @ManyToOne(() => HomeInspectionEntity)
  inspection?: HomeInspectionEntity;

  toAggregate(publisher?: EventPublisher): HomeInspectionGuaranteeAggregate {
    return mergeObjectContext(
      new HomeInspectionGuaranteeAggregate({
        id: this.id,
        referenceId: this.referenceId,

        status: this.status,

        type: this.type,

        created: this.created,
        modified: this.modified,

        contractNumber: this.contractNumber,

        termStart: this.termStart,
        termDuration: this.termDuration,

        assetId: this.assetId,
        asset: this.asset instanceof HomeAssetEntity ? this.asset.toAggregate(publisher) : undefined,

        policyId: this.policyId,
        policy: this.policy?.toAggregate(publisher) ?? undefined,

        customerId: this.customerId,
        customer: this.customer?.toAggregate(publisher) ?? undefined,

        inspectionId: this.inspectionId,
        inspection: this.inspection?.toAggregate(publisher) ?? undefined,
      }),
      publisher
    );
  }
}
