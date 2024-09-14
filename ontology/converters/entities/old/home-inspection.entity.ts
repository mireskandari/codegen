import { EventPublisher } from '@nestjs/cqrs';
import { mergeObjectContext, VsolvChildEntity } from '@vsolv/dev-kit/nest';
import { HomeInspection } from '@wsphere/homes/domain';
import { InspectionEntity } from '@wsphere/inspections/api';
import { Column, JoinColumn, ManyToOne } from 'typeorm';
import { HomeAssetEntity } from '../../home-asset';
import { HomeInspectionAggregate } from '../models';

@VsolvChildEntity('home', 'tenant')
export class HomeInspectionEntity extends InspectionEntity<'home'> implements HomeInspection.Model {
  @Column()
  structuralCondition!: boolean;
  @Column()
  nonStructuralCondition!: boolean;

  @JoinColumn({ name: 'assetId' })
  @ManyToOne(() => HomeAssetEntity)
  asset?: HomeAssetEntity;

  toAggregate(publisher?: EventPublisher): HomeInspectionAggregate {
    return mergeObjectContext(
      new HomeInspectionAggregate({
        id: this.id,
        referenceId: this.referenceId,

        timestamp: this.timestamp,

        type: this.type,

        assetId: this.assetId,
        asset: this.asset?.toAggregate(publisher) ?? undefined,

        customerId: this.customerId,
        customer: this.customer?.toAggregate(publisher) ?? undefined,

        inspectorId: this.inspectorId,
        inspector: this.inspector?.toAggregate(publisher) ?? undefined,

        structuralCondition: this.structuralCondition,
        nonStructuralCondition: this.nonStructuralCondition,
      }),
      publisher
    );
  }
}
